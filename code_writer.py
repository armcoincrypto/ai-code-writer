#!/usr/bin/env python3
"""
ai-code-writer: generate complete Python scripts via your chosen AI model.

Key features:
  - Syntax check:     --syntax-check  (py_compile)
  - Formatting:       --format (isort + black)
  - Providers:        --provider stub|openai|auto
                      * openai: OpenAI-compatible (works with OpenAI cloud
                        or Ollama via OPENAI_BASE_URL + OPENAI_API_KEY=ollama)
                      * auto: try openai; on error → safe stub
  - Exec sandbox:     --exec-test + --exec-args
  - Tests:            --with-tests  --expect-output "..."  --test-args "..."
                      --run-tests
"""
from __future__ import annotations

import argparse
import os
import py_compile
import re
import shlex
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ───────────────────────── helpers ─────────────────────────


def run_syntax_check(path: str) -> tuple[bool, str]:
    """Check Python syntax."""
    try:
        py_compile.compile(path, doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, str(e)


@dataclass
class WriteResult:
    path: str
    code: str


def ensure_dir(path: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def write_code(path: str, code: str) -> WriteResult:
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code.rstrip() + "\n")
    return WriteResult(path, code)


# ───────────────────── prompt & extraction ─────────────────────
_CODE_FENCE = re.compile(r"```(?:python)?\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code_blocks(text: str) -> str:
    """
    Take model text and return the first Python fenced block, or the raw text
    trimmed to a plausible Python start.
    """
    m = _CODE_FENCE.search(text or "")
    snippet = (m.group(1) if m else (text or "")).strip()
    lines = snippet.splitlines()
    while lines and not lines[0].lstrip().startswith(
        ("import ", "from ", "def ", "class ", "#", "#!", "if __name__")
    ):
        lines.pop(0)
    return "\n".join(lines).strip()


def make_prompt(task: str) -> str:
    return textwrap.dedent(
        f"""
        You are an expert Python 3.11+ developer.
        Write a COMPLETE, RUNNABLE single-file Python program that accomplishes:

        TASK:
        {task}

        REQUIREMENTS:
        - Include a main() and if __name__ == '__main__' guard.
        - Use only the standard library unless the task truly needs deps.
        - Return ONLY a single fenced Python code block.
        """
    ).strip()


# ───────────────────── providers (openai + stub) ─────────────────────
def _stub_script(note: str = "Stub fallback") -> str:
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env python3
        \"\"\"{note}\"\"\"
        import sys

        def main() -> None:
            print('STUB')
            print('Args:', sys.argv[1:])

        if __name__ == '__main__':
            main()
        """
    )


def have_openai_credentials() -> bool:
    """
    True if we have an API key. OPENAI_BASE_URL may or may not be set.
    When pointing to Ollama, set:
      OPENAI_BASE_URL=http://127.0.0.1:11434/v1
      OPENAI_API_KEY=ollama
    """
    return bool(os.getenv("OPENAI_API_KEY"))


class OpenAIProvider:
    """
    OpenAI-compatible client (works with OpenAI cloud or Ollama via base_url).
    """

    def __init__(self, model: str, temperature: float) -> None:
        try:
            from openai import OpenAI
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"openai package missing: {e}") from e

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY")

        if base_url:
            self._client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self._client = OpenAI(api_key=api_key)

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature

    def generate(self, prompt: str, max_tokens: int) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=max_tokens,
            )
            text = resp.choices[0].message.content or ""
            code = extract_code_blocks(text) or _stub_script("No code block extracted")
            return code
        except Exception as e:
            print(f"⚠️ OpenAI error: {e} — using stub.", file=sys.stderr)
            return _stub_script("OpenAI error")


def generate_with_provider(
    provider: str,
    prompt: str,
    model: str,
    temp: float,
    max_tokens: int,
) -> str:
    """
    provider:
      - 'openai': use OpenAI-compatible client; on any error → stub
      - 'stub':   always stub
      - 'auto':   try openai (if creds) else stub
    """
    if provider == "openai":
        try:
            return OpenAIProvider(model, temp).generate(prompt, max_tokens)
        except Exception as e:
            print(f"⚠️ Provider init failed: {e} — stub.", file=sys.stderr)
            return _stub_script("Provider init failed")

    if provider == "auto":
        if have_openai_credentials():
            try:
                return OpenAIProvider(model, temp).generate(prompt, max_tokens)
            except Exception as e:
                print(f"⚠️ auto/openai failed: {e} — stub.", file=sys.stderr)
        return _stub_script("auto fallback: no usable provider")

    # default stub
    return _stub_script("Stub provider")


# ─────────────────────── formatting ────────────────────────
def run_formatting(path: str) -> None:
    try:
        subprocess.run([sys.executable, "-m", "isort", path], check=True)
        subprocess.run([sys.executable, "-m", "black", path], check=True)
        print(f"🔧 Formatted {path}")
    except Exception as e:
        print(f"⚠️ Formatting failed: {e}", file=sys.stderr)


# ───────────────────── tests (writer & runner) ──────────────────────
def write_pytest_for_script(
    script_path: str,
    expect_contains: Optional[str],
    test_args: str,
) -> str:
    """
    Create test_<script>.py that runs the generated script with provided args,
    asserts returncode==0, and optionally checks stdout contains a substring.
    """
    p = Path(script_path)
    test_path = str(p.with_name(f"test_{p.stem}.py"))

    # keep shlex.split in test to handle quoted strings in --test-args
    content = textwrap.dedent(
        f"""\
        import pathlib
        import shlex
        import subprocess
        import sys

        TEST_ARGS = {test_args!r}

        def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                argv, capture_output=True, text=True, timeout=30
            )

        def test_script_runs_ok() -> None:
            script = pathlib.Path(__file__).with_name({p.name!r})
            args = [sys.executable, str(script)]
            if TEST_ARGS:
                args += shlex.split(TEST_ARGS)
            cp = _run(args)
            assert cp.returncode == 0, cp.stderr
        """
    )

    if expect_contains:
        content += textwrap.dedent(
            f"""
            def test_output_contains_expected_substring() -> None:
                script = pathlib.Path(__file__).with_name({p.name!r})
                args = [sys.executable, str(script)]
                if TEST_ARGS:
                    args += shlex.split(TEST_ARGS)
                cp = _run(args)
                assert {expect_contains!r} in cp.stdout
            """
        )

    with open(test_path, "w", encoding="utf-8") as f:
        f.write(content)
    return test_path


def run_pytests(test_path: str) -> int:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", test_path],
            capture_output=True,
            text=True,
        )
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.returncode != 0 and proc.stderr:
            print(proc.stderr, end="")
        return proc.returncode
    except FileNotFoundError:
        print("⚠️ pytest not installed. pip install pytest", file=sys.stderr)
        return 127


# ─────────────────────────── CLI ───────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Python code via AI.")
    parser.add_argument(
        "--provider",
        choices=["stub", "openai", "auto"],
        required=True,
        help="Model provider or auto fallback",
    )
    parser.add_argument("--model", help="Model name (OpenAI or compatible)")
    parser.add_argument("--task", required=True, help="Natural-language code task")
    parser.add_argument("--out", required=True, help="Output file path")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=6000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", action="store_true", help="Run isort + black")
    parser.add_argument("--syntax-check", action="store_true")
    parser.add_argument("--exec-test", action="store_true", help="Run script once")
    parser.add_argument(
        "--exec-args",
        default="",
        help='Args for the script during run (e.g. "--foo 1 --bar baz")',
    )
    parser.add_argument("--post-cmd", help="Shell command to run after writing")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--quiet", action="store_true")

    # new testing flags
    parser.add_argument(
        "--with-tests",
        action="store_true",
        help="Write a pytest file for the generated script",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run pytest for the generated test file",
    )
    parser.add_argument(
        "--expect-output",
        help="Assert stdout contains this text during tests",
    )
    parser.add_argument(
        "--test-args",
        default="--help",
        help="Args to use when running tests (default: --help)",
    )

    args = parser.parse_args()

    def log(msg: str) -> None:
        if not args.quiet:
            print(msg)

    prompt = make_prompt(args.task)

    code = generate_with_provider(
        args.provider, prompt, args.model or "", args.temperature, args.max_tokens
    )
    if args.dry_run:
        print(code)
        return

    wr = write_code(args.out, code)
    print(f"✅ Wrote {wr.path}")

    if args.format:
        run_formatting(wr.path)

    if args.syntax_check:
        ok, err = run_syntax_check(wr.path)
        if not ok:
            print(err)

    # optional test file generation
    test_path: Optional[str] = None
    if args.with_tests:
        test_path = write_pytest_for_script(wr.path, args.expect_output, args.test_args)
        print(f"🧪 Wrote {test_path}")
        if args.format:
            run_formatting(test_path)

    # optional run pytest
    if args.run_tests:
        if not test_path:
            test_path = write_pytest_for_script(
                wr.path, args.expect_output, args.test_args
            )
            print(f"🧪 Wrote {test_path}")
            if args.format:
                run_formatting(test_path)
        rc = run_pytests(test_path)
        if rc != 0:
            log("⚠️ Tests failed. See output above.")

    # Exec sandbox (optional single run)
    if args.exec_test:
        log(f"🧪 Executing {wr.path} with args: {args.exec_args}")
        cmd = [sys.executable, wr.path]
        if args.exec_args:
            cmd += shlex.split(args.exec_args)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)

    # Post-cmd
    if args.post_cmd and not args.quiet:
        try:
            subprocess.run(args.post_cmd, shell=True, check=True)
            print(f"🔗 Ran post-cmd: {args.post_cmd}")
        except Exception as e:
            log(f"⚠️ Post-cmd failed: {e}")


if __name__ == "__main__":
    main()
