#!/usr/bin/env python3
"""
ai-code-writer: generate complete Python scripts via your chosen AI model.

Key features:
  - Syntax check:         --syntax-check  (py_compile)
  - Deps management:      --requirements  --install-deps
  - Domain templates:     --domain fastapi|pandas|pytorch|click|aiogram
  - Lint/typing:          --lint (flake8)  --typecheck (mypy)
  - Auto-fix loop:        --fix N  (uses flake8/mypy/pytest diagnostics)
  - Tests:                --with-tests  --expect-output "..."  --run-tests
  - Provider rotation:    auto-rotate on stub/error (Gemini/OpenAI/Anthropic)
  - Execution sandbox:    --exec-test
  - Formatting:           --format (isort + black)

Install (once):
  pip install openai anthropic google-generativeai python-dotenv \
              black isort pytest flake8 mypy
"""
import argparse
import os
import py_compile
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# --- safe accessor for union content blocks ---
def _safe_text(x: object) -> str:
    t = getattr(x, "text", None)
    return t if isinstance(t, str) else ""


# ── .env loader ──────────────────────────────────────────────────────
try:
    from pathlib import Path

    from dotenv import load_dotenv

    _here = Path(__file__).parent
    load_dotenv(_here / ".env")
except Exception:
    pass


# ── Prompt & domain guidance ─────────────────────────────────────────
def get_prompt_template(name: str, task: str) -> str:
    templates = {
        "basic": textwrap.dedent(
            f"""
            You are an expert Python 3.11+ developer.
            Write a COMPLETE, RUNNABLE single-file Python program that does:

            TASK:
            {task}

            Include main() and if __name__ == '__main__'.
            """
        ),
        "production": textwrap.dedent(
            f"""
            You are a senior Python engineer.
            Write a production-ready Python 3.11+ module that accomplishes:

            TASK:
            {task}

            REQUIREMENTS:
            - Robust error handling & logging
            - Type annotations & docstrings
            - Include unit tests or doctests
            - Provide setup instructions
            """
        ),
        "tested": textwrap.dedent(
            f"""
            You are a Python developer focused on testing.
            Create a Python 3.11+ script and a corresponding pytest file for:

            TASK:
            {task}

            REQUIREMENTS:
            - Script with main() and argparse
            - Separate test file using pytest
            - Tests cover edge cases
            """
        ),
    }
    return templates.get(name, templates["basic"]).strip()


def get_domain_guidance(domain: Optional[str]) -> str:
    if not domain:
        return ""
    guides = {
        "fastapi": textwrap.dedent(
            """
            DOMAIN:
            - Use FastAPI. Provide a main FastAPI app with path operations.
            - Add a '/debug' GET route that returns selected environment keys
              (filter out secrets: keys containing 'KEY', 'TOKEN', 'SECRET', 'PASS').
            - Provide uvicorn run instructions in __main__.
            - Use Pydantic models and type hints.
            - Keep handlers small and documented.
            """
        ),
        "pandas": textwrap.dedent(
            """
            DOMAIN:
            - Use pandas idioms (read_csv, groupby, assign, pipe).
            - stdin-safe: if no args, only read stdin when data is present;
              otherwise fall back to a tiny demo DataFrame.
            - Include CLI args for input/output paths.
            """
        ),
        "pytorch": textwrap.dedent(
            """
            DOMAIN:
            - Use a tiny PyTorch training loop that runs fast (small model/batch).
            - Set seeds; device = cuda if available else cpu.
            - Provide a __main__ entry that trains for a few steps and prints metrics.
            """
        ),
        "click": textwrap.dedent(
            """
            DOMAIN:
            - Use Click for CLI with clear options and help.
            - Provide a single entry command and subcommands if useful.
            """
        ),
        "aiogram": textwrap.dedent(
            """
            DOMAIN:
            - Use aiogram 3.x. Provide a minimal bot with router/handlers.
            - Add a '/debug' command/handler that logs safe env keys
              (filter secrets) without leaking tokens.
            - Structure for clean shutdown and error handling.
            """
        ),
    }
    return guides.get(domain, "")


# ── Extract Python code from model output ────────────────────────────
_CODE_FENCE = re.compile(r"```(?:python)?\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code_blocks(text: str) -> str:
    m = _CODE_FENCE.search(text or "")
    snippet = (m.group(1) if m else (text or "")).strip()
    lines = snippet.splitlines()
    while lines and not lines[0].lstrip().startswith(
        ("import ", "from ", "def ", "class ", "#", "#!", "if __name__")
    ):
        lines.pop(0)
    return "\n".join(lines).strip()


# ── File ops & formatting ────────────────────────────────────────────
def ensure_dir(path: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


@dataclass
class WriteResult:
    path: str
    code: str


def write_code(path: str, code: str) -> WriteResult:
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code.rstrip() + "\n")
    return WriteResult(path, code)


def run_formatting(path: str) -> None:
    try:
        subprocess.run([sys.executable, "-m", "isort", path], check=True)
        subprocess.run([sys.executable, "-m", "black", path], check=True)
        print(f"🔧 Formatted {path}")
    except Exception as e:
        print(f"⚠️ Formatting failed: {e}")


def run_syntax_check(path: str) -> Tuple[bool, str]:
    try:
        py_compile.compile(path, doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, str(e)


# ── Linting & typing ────────────────────────────────────────────────
def run_flake8(path: str) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            [sys.executable, "-m", "flake8", path], capture_output=True, text=True
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "flake8 not installed. Install with: pip install flake8"


def run_mypy(path: str) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            [sys.executable, "-m", "mypy", path], capture_output=True, text=True
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "mypy not installed. Install with: pip install mypy"


# ── Requirements management ─────────────────────────────────────────
def get_requirements_for_domain(domain: Optional[str]) -> List[str]:
    if not domain:
        return []
    reqs: Dict[str, List[str]] = {
        "pandas": ["pandas>=2.2"],
        "fastapi": ["fastapi>=0.112", "uvicorn>=0.30"],
        "click": ["click>=8.1"],
        "pytorch": [
            "torch>=2.2; platform_system!='Darwin' or platform_machine!='arm64'"
        ],  # skip heavy MPS nuance
        "aiogram": ["aiogram>=3.4"],
    }
    return reqs.get(domain, [])


def write_requirements(
    reqs: List[str], path: str = "requirements.txt"
) -> Optional[str]:
    if not reqs:
        return None
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(reqs) + "\n")
    return path


def install_requirements(req_path: str) -> int:
    try:
        p = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path], text=True
        )
        return p.returncode
    except Exception:
        return 1


# ── Providers ───────────────────────────────────────────────────────
@dataclass
class ProviderResult:
    text: str


class GeminiProvider:
    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing GOOGLE_API_KEY (or GEMINI_API_KEY)")
        import google.generativeai as genai

        self._genai = genai
        self._genai.configure(api_key=self.api_key)

    def generate(self, prompt: str, max_tokens: int) -> ProviderResult:
        from google.api_core.exceptions import ResourceExhausted

        fenced = "```python\n" + prompt + "\n```"
        try:
            resp = self._genai.GenerativeModel(self.model).generate_content(fenced)
            code = getattr(resp, "text", "") or str(resp)
        except ResourceExhausted:
            print("⚠️ Gemini quota exhausted—using safe stub.")
            return ProviderResult(text=(make_stub("Gemini quota exhausted." or "")))
        except Exception as e:
            try:
                default = os.getenv("GEMINI_MODEL", "models/gemini-2.5-pro")
                print(f"⚠️ Gemini error ({e}); retrying '{default}'…")
                resp = self._genai.GenerativeModel(default).generate_content(fenced)
                code = getattr(resp, "text", "") or str(resp)
            except Exception as e2:
                print(f"⚠️ Gemini fallback failed ({e2})—using safe stub.")
                return ProviderResult(
                    text=(make_stub("Gemini error; fallback failed." or ""))
                )
        return ProviderResult(text=(code or ""))


class OpenAIProvider:
    def __init__(self, model: str, temperature: float):
        self.model = model
        self.temperature = temperature
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing OPENAI_API_KEY")
        from openai import OpenAI

        self._client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, max_tokens: int) -> ProviderResult:
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=max_tokens,
            )
            return ProviderResult(text=(resp.choices[0].message.content or ""))
        except Exception as e:
            print(f"⚠️ OpenAI error: {e} — using safe stub.")
            return ProviderResult(text=(make_stub("OpenAI error." or "")))


class AnthropicProvider:
    def __init__(self, model: str, temperature: float):
        self.model = model
        self.temperature = temperature
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY")
        import anthropic

        self._client = anthropic.Anthropic(api_key=self.api_key)

    def generate(self, prompt: str, max_tokens: int) -> ProviderResult:
        try:
            msg = self._client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=self.temperature,
            )
            parts = [
                _safe_text(p) for p in msg.content if getattr(p, "type", "") == "text"
            ]
            return ProviderResult(text=("".join(parts or "")) if parts else str(msg))
        except Exception as e:
            print(f"⚠️ Anthropic error: {e} — using safe stub.")
            return ProviderResult(text=(make_stub("Anthropic error." or "")))


PROVIDERS = {
    "gemini": (GeminiProvider, 0),
    "openai": (OpenAIProvider, 1),
    "anthropic": (AnthropicProvider, 1),
}


# ── Stub generator (always-valid Python) ────────────────────────────
def make_stub(note: Optional[str] = None) -> str:
    note_line = (note or "Stub fallback generated by ai-code-writer.").replace(
        "\n", " "
    )
    return (
        "#!/usr/bin/env python3\n"
        "'''\n"
        f"{note_line}\n"
        "'''\n\n"
        "def main() -> None:\n"
        "    # TODO: replace stub with real implementation\n"
        "    print('STUB')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )


# ── Pytest generation ───────────────────────────────────────────────
def write_pytest_for_script(
    script_path: str, expect_contains: Optional[str], domain: Optional[str]
) -> str:
    import pathlib

    p = pathlib.Path(script_path)
    test_path = str(p.with_name(f"test_{p.stem}.py"))

    if domain == "pandas":
        content = (
            "import csv, pathlib, subprocess, sys, tempfile\n\n"
            "def test_script_runs():\n"
            f"    script = pathlib.Path(__file__).with_name('{p.name}')\n"
            "    with tempfile.TemporaryDirectory() as td:\n"
            "        path = pathlib.Path(td) / 'd.csv'\n"
            "        with path.open('w', newline='') as f:\n"
            "            w = csv.DictWriter(f, fieldnames=['value'])\n"
            "            w.writeheader(); w.writerows([{'value':1},{'value':2},{'value':3}])\n"
            "        proc = subprocess.run([sys.executable, str(script), str(path)], capture_output=True, text=True, timeout=10)\n"
            "        assert proc.returncode == 0\n"
        )
    else:
        content = (
            "import subprocess, sys, pathlib\n\n"
            "def test_script_runs():\n"
            f"    script = pathlib.Path(__file__).with_name('{p.name}')\n"
            "    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=10)\n"
            "    assert proc.returncode == 0\n"
        )

    if expect_contains:
        content += f"    assert {expect_contains!r} in proc.stdout\n"

    with open(test_path, "w", encoding="utf-8") as f:
        f.write(content)
    return test_path


def run_pytests(test_path: str) -> int:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", test_path],
            capture_output=True,
            text=True,
        )
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.returncode != 0 and completed.stderr:
            print(completed.stderr, end="")
        return completed.returncode
    except FileNotFoundError:
        print("⚠️ pytest not installed. Install with: pip install pytest")
        return 127


# ── Diagnostics & fix loop ──────────────────────────────────────────
def run_checks(path: str, do_lint: bool, do_mypy: bool) -> Tuple[bool, str]:
    ok = True
    parts: List[str] = []

    # syntax
    syn_ok, syn_err = run_syntax_check(path)
    if not syn_ok:
        ok = False
        parts.append("# syntax\n" + syn_err)

    # flake8
    if do_lint:
        rc, out, err = run_flake8(path)
        if rc not in (0, 127):
            ok = False
        if out:
            parts.append("# flake8\n" + out)
        if err and rc != 0:
            parts.append("# flake8-stderr\n" + err)
        if rc == 127:
            parts.append(
                "# flake8\nflake8 not installed. Install with: pip install flake8\n"
            )

    # mypy
    if do_mypy:
        rc, out, err = run_mypy(path)
        if rc not in (0, 127):
            ok = False
        if out:
            parts.append("# mypy\n" + out)
        if err and rc != 0:
            parts.append("# mypy-stderr\n" + err)
        if rc == 127:
            parts.append("# mypy\nmypy not installed. Install with: pip install mypy\n")

    return ok, "\n".join(parts).strip()


def refine_with_feedback(
    provider, current_code: str, diagnostics: str, max_tokens: int
) -> str:
    feedback_prompt = textwrap.dedent(
        f"""
        You previously wrote this Python file:

        ```python
        {current_code}
        ```

        Tool diagnostics to fix:
        {diagnostics}

        Please return a corrected, COMPLETE single-file Python 3.11+ program that resolves these issues.
        Only return one fenced Python code block.
        """
    ).strip()
    result = provider.generate(feedback_prompt, max_tokens)
    code = extract_code_blocks(_safe_text(result))
    return code or make_stub("Fix attempt produced no code.")


# ── Provider rotation ───────────────────────────────────────────────
def is_stub(code: str) -> bool:
    return "print('STUB')" in code or "Stub fallback" in code


def rotate_providers_order(primary: str) -> List[str]:
    order = ["gemini", "openai", "anthropic"]
    if primary in order:
        order.remove(primary)
        return [primary] + order
    return order


def generate_with_rotation(
    primary: str, prompt: str, model_name: str, temp: float, max_tokens: int
) -> str:
    order = rotate_providers_order(primary)
    last_code = ""
    for provider_name in order:
        try:
            prov_cls, needs_temp = PROVIDERS[provider_name]
            provider = (
                prov_cls(model_name, temp) if needs_temp else prov_cls(model_name)
            )
            print(f"➡️ Using {provider_name} model: {model_name}")
            result = provider.generate(prompt, max_tokens)
            code = extract_code_blocks(_safe_text(result)) or make_stub(
                "No code block extracted."
            )
            if not is_stub(code):
                return code
            last_code = code
            print(f"⚠️ {provider_name} returned stub; trying next provider…")
        except Exception as e:
            print(f"⚠️ Provider {provider_name} failed: {e}")
            continue
    return last_code or make_stub("All providers failed or returned stubs.")


# ── CLI ─────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Python code via AI.")
    ap.add_argument("--provider", choices=PROVIDERS, required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--out", default="generated.py")
    ap.add_argument(
        "--prompt-template", choices=["basic", "production", "tested"], default="basic"
    )
    ap.add_argument(
        "--domain",
        choices=["fastapi", "pandas", "pytorch", "click", "aiogram"],
        help="Domain guidance",
    )
    ap.add_argument("--model", help="Override model name for provider")
    ap.add_argument(
        "--temperature", type=float, default=0.2, help="OpenAI/Anthropic only"
    )
    ap.add_argument("--max-tokens", type=int, default=6000)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--format", action="store_true")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--typecheck", action="store_true")
    ap.add_argument("--syntax-check", action="store_true")
    ap.add_argument(
        "--requirements", action="store_true", help="Emit requirements.txt for domain"
    )
    ap.add_argument(
        "--install-deps", action="store_true", help="pip install -r requirements.txt"
    )
    ap.add_argument(
        "--fix", type=int, default=0, help="Auto-fix iterations using diagnostics"
    )
    ap.add_argument(
        "--exec-test", action="store_true", help="Run the generated code in a sandbox"
    )
    ap.add_argument(
        "--with-tests",
        action="store_true",
        help="Generate a pytest file alongside the script",
    )
    ap.add_argument(
        "--expect-output", help="Assert stdout contains this text during tests"
    )
    ap.add_argument(
        "--run-tests", action="store_true", help="Run pytest on the generated test file"
    )
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--verbose", action="store_true")
    grp.add_argument("--quiet", action="store_true")
    ap.add_argument("--post-cmd", help="Shell command after writing")
    args = ap.parse_args()

    def log(msg: str) -> None:
        if not args.quiet:
            print(msg)

    def debug(msg: str) -> None:
        if args.verbose and not args.quiet:
            print(msg)

    # Resolve model (with sane defaults)
    default_models = {
        "gemini": "models/gemini-2.5-pro",
        "openai": "gpt-3.5-turbo",
        "anthropic": "claude-3-5-sonnet-20240620",
    }
    model_name = (
        args.model
        or os.getenv(f"{args.provider.upper()}_MODEL")
        or default_models[args.provider]
    )

    # Build prompt
    base_prompt = get_prompt_template(args.prompt_template, args.task)
    domain_extra = get_domain_guidance(args.domain)
    prompt = base_prompt + (("\n\n" + domain_extra) if domain_extra else "")

    # Requirements
    reqs = get_requirements_for_domain(args.domain)
    if args.requirements:
        req_path = write_requirements(reqs)  # may be None
        if req_path:
            print(f"📦 Wrote {req_path}")
            if args.install_deps:
                rc = install_requirements(req_path)
                if rc != 0:
                    print("⚠️ Dependency installation failed (see logs).")

    # Generate with rotation (avoids getting stuck on stubs)
    code = generate_with_rotation(
        args.provider, prompt, model_name, args.temperature, args.max_tokens
    )

    if args.dry_run:
        print(code)
        return

    # Write + format
    wr = write_code(args.out, code)
    print(f"✅ Wrote {wr.path}")
    if args.format:
        run_formatting(wr.path)

    # Syntax check (fast & precise)
    if args.syntax_check:
        syn_ok, syn_err = run_syntax_check(wr.path)
        if not syn_ok:
            print("# syntax\n" + syn_err)

    # Lint/typecheck and optional fix loop (also can include pytest failures)
    diagnostics = []
    ok, diag = run_checks(wr.path, args.lint, args.typecheck)
    if diag:
        print(diag)
        diagnostics.append(diag)

    # Tests (optional)
    test_path = None
    if args.with_tests:
        test_path = write_pytest_for_script(wr.path, args.expect_output, args.domain)
        print(f"🧪 Wrote {test_path}")
        if args.format:
            run_formatting(test_path)

    test_rc = 0
    if args.run_tests:
        if not test_path:
            # fabricate a generic test if user asked to run tests without --with-tests
            test_path = write_pytest_for_script(
                wr.path, args.expect_output, args.domain
            )
            print(f"🧪 Wrote {test_path}")
        test_rc = run_pytests(test_path)
        if test_rc != 0:
            diagnostics.append("# pytest\nTests failed. See output above.")

    # Fix loop
    iter_left = max(0, int(args.fix))
    while iter_left > 0 and (not ok or test_rc != 0):
        debug(f"♻️ Auto-fix iteration (remaining: {iter_left})")
        combined = "\n\n".join(diagnostics).strip() or "No diagnostics available."
        new_code = refine_with_feedback(
            provider=(
                GeminiProvider(model_name)
                if args.provider == "gemini"
                else (
                    OpenAIProvider(model_name, args.temperature)
                    if args.provider == "openai"
                    else AnthropicProvider(model_name, args.temperature)
                )
            ),
            current_code=wr.code,
            diagnostics=combined,
            max_tokens=args.max_tokens,
        )
        wr = write_code(args.out, new_code)
        if args.format:
            run_formatting(wr.path)

        ok, diag = run_checks(wr.path, args.lint, args.typecheck)
        diagnostics = [diag] if diag else []
        if args.run_tests:
            if not test_path:
                test_path = write_pytest_for_script(
                    wr.path, args.expect_output, args.domain
                )
            test_rc = run_pytests(test_path)
            if test_rc != 0:
                diagnostics.append("# pytest\nTests failed. See output above.")
        iter_left -= 1

    if (args.lint or args.typecheck or args.run_tests) and (not ok or test_rc != 0):
        log("⚠️ Diagnostics remain after fixes. Inspect output above.")

    # Exec sandbox (optional)
    if args.exec_test:
        log(f"🧪 Executing {wr.path} in sandbox...")
        try:
            proc = subprocess.run(
                [sys.executable, wr.path], capture_output=True, text=True, timeout=10
            )
            if proc.returncode != 0:
                print("❌ Execution failed:")
                print(proc.stderr)
            else:
                print("✅ Execution succeeded:")
                print(proc.stdout, end="")
        except Exception as e:
            print(f"⚠️ Sandbox error: {e}")

    # Post-cmd
    if args.post_cmd and not args.quiet:
        try:
            subprocess.run(args.post_cmd, shell=True, check=True)
            print(f"🔗 Ran post-cmd: {args.post_cmd}")
        except Exception as e:
            debug(f"Post-cmd failed: {e}")


if __name__ == "__main__":
    main()
