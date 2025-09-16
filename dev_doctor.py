#!/usr/bin/env python3
"""
dev_doctor: sanity-check your Python toolchain, repo hygiene, and ai-code-writer.

- Verifies: Python>=3.11, venv active, CLI tools (isort/black/flake8/mypy/pytest/pre-commit),
  OpenAI client (optional), Ollama (optional), .env hygiene, pre-commit hook presence,
  and a live smoke-test of code_writer.py with --exec-args.
- Exits non-zero if any MANDATORY checks fail.

Usage:
  python3 dev_doctor.py              # quick (no network calls)
  python3 dev_doctor.py --full       # includes optional OpenAI/Ollama checks
  python3 dev_doctor.py --run-verify # also runs `make verify` if available
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, List, Tuple

MANDATORY_TOOLS: Tuple[str, ...] = (
    "isort",
    "black",
    "flake8",
    "mypy",
    "pytest",
    "pre_commit",
)
OPTIONAL_PY_MODULES: Tuple[str, ...] = ("openai", "dotenv")
OPTIONAL_BINARIES: Tuple[str, ...] = ("ollama",)
CODE_WRITER = "code_writer.py"


@dataclass
class Check:
    name: str
    ok: bool
    msg: str = ""
    mandatory: bool = True


def _ok_icon(ok: bool) -> str:
    return "✅" if ok else "❌"


def _warn_icon() -> str:
    return "⚠️"


def run_cmd(args: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def in_venv() -> bool:
    return (
        sys.prefix != getattr(sys, "base_prefix", sys.prefix)
        or os.environ.get("VIRTUAL_ENV") is not None
    )


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def python_meets_requirement(min_major: int = 3, min_minor: int = 11) -> bool:
    return sys.version_info >= (min_major, min_minor)


def has_module(mod: str) -> Tuple[bool, str]:
    try:
        module = __import__(mod)
        version = getattr(module, "__version__", "")
        return True, str(version)
    except Exception as e:
        return False, str(e)


def check_python() -> Check:
    ok = python_meets_requirement()
    return Check(
        "Python >= 3.11", ok, msg=f"Running {sys.version.split()[0]}", mandatory=True
    )


def check_venv() -> Check:
    ok = in_venv()
    return Check(
        "Virtualenv active",
        ok,
        msg=(
            "VIRTUAL_ENV is set" if ok else "Activate venv: source .venv/bin/activate"
        ),
        mandatory=True,
    )


def check_cli_tools() -> List[Check]:
    checks: List[Check] = []
    for tool in MANDATORY_TOOLS:
        path = which(tool.replace("_", "-")) or which(tool)
        ok = path is not None
        checks.append(
            Check(f"{tool} available", ok, msg=(path or "not found"), mandatory=True)
        )
    return checks


def check_optional_modules() -> List[Check]:
    out: List[Check] = []
    for mod in OPTIONAL_PY_MODULES:
        ok, info = has_module(mod)
        out.append(Check(f"python -m {mod}", ok, msg=(info or "OK"), mandatory=False))
    return out


def check_optional_bins() -> List[Check]:
    out: List[Check] = []
    for b in OPTIONAL_BINARIES:
        path = which(b)
        out.append(
            Check(
                f"{b} installed",
                path is not None,
                msg=(path or "not found"),
                mandatory=False,
            )
        )
    return out


def check_env_hygiene() -> List[Check]:
    checks: List[Check] = []
    env_path = os.path.join(os.getcwd(), ".env")
    env_example = os.path.join(os.getcwd(), ".env.example")
    checks.append(
        Check(".env.example present", os.path.exists(env_example), mandatory=False)
    )
    checks.append(
        Check(".env present (local only)", os.path.exists(env_path), mandatory=False)
    )

    # ensure .env is not tracked
    try:
        cp = run_cmd(["git", "ls-files", "--error-unmatch", ".env"], timeout=5)
        tracked = cp.returncode == 0
    except Exception:
        tracked = False

    checks.append(
        Check(
            ".env not tracked by git",
            ok=not tracked,
            msg=("tracked by git" if tracked else "ignored/absent"),
            mandatory=True if tracked else False,
        )
    )
    return checks


def check_precommit_installed() -> Check:
    hook = os.path.join(".git", "hooks", "pre-commit")
    ok = os.path.exists(hook)
    return Check(
        "pre-commit hook installed",
        ok,
        msg=(hook if ok else "Run: pre-commit install"),
        mandatory=False,
    )


def code_writer_smoke(provider: str = "stub") -> Check:
    """
    Generate a tiny script and execute with --exec-args to confirm our
    code_writer flow and sandbox work end-to-end.
    """
    if not os.path.exists(CODE_WRITER):
        return Check(
            "code_writer.py present",
            False,
            msg="Missing code_writer.py",
            mandatory=True,
        )

    out = "doctor_exec_test.py"
    try:
        args = [
            sys.executable,
            CODE_WRITER,
            "--provider",
            provider,
            "--task",
            "print('HI'); import sys; print('Args:', sys.argv[1:])",
            "--out",
            out,
            "--exec-test",
            "--exec-args",
            "--foo 1 --bar baz",
        ]
        cp = run_cmd(args, timeout=40)
        ok = (cp.returncode == 0) and (
            "Args: ['--foo', '1', '--bar', 'baz']" in (cp.stdout + cp.stderr)
        )
        msg = "ok" if ok else f"return={cp.returncode}"
        return Check("code_writer smoke (--exec-args)", ok, msg=msg, mandatory=True)
    finally:
        try:
            if os.path.exists(out):
                os.remove(out)
        except Exception:
            pass


def make_verify() -> Check:
    makefile_exists = os.path.exists("Makefile")
    if not makefile_exists:
        return Check(
            "Makefile present", False, msg="No Makefile in repo root", mandatory=False
        )
    try:
        cp = run_cmd(["make", "verify"], timeout=240)
        ok = cp.returncode == 0
        return Check("make verify", ok, msg=("OK" if ok else "failed"), mandatory=False)
    except Exception as e:
        return Check("make verify", False, msg=str(e), mandatory=False)


def print_report(checks: Iterable[Check]) -> tuple[int, int, int]:
    total = 0
    failures = 0
    warnings = 0
    for c in checks:
        total += 1
        icon = (
            _ok_icon(c.ok)
            if c.mandatory
            else (_ok_icon(c.ok) if c.ok else _warn_icon())
        )
        print(f"{icon} {c.name} — {c.msg}")
        if c.mandatory and not c.ok:
            failures += 1
        if not c.mandatory and not c.ok:
            warnings += 1
    return total, failures, warnings


def main() -> None:
    ap = argparse.ArgumentParser(description="Project doctor for ai-code-writer.")
    ap.add_argument(
        "--full", action="store_true", help="Run optional OpenAI/Ollama checks"
    )
    ap.add_argument("--run-verify", action="store_true", help="Also run `make verify`")
    ap.add_argument(
        "--provider",
        choices=["stub", "openai"],
        default="stub",
        help="Provider for code_writer smoke-test",
    )
    args = ap.parse_args()

    checks: List[Check] = []
    checks.append(check_python())
    checks.append(check_venv())
    checks.extend(check_cli_tools())
    checks.extend(check_env_hygiene())
    checks.append(check_precommit_installed())

    if args.full:
        checks.extend(check_optional_modules())
        checks.extend(check_optional_bins())

    checks.append(code_writer_smoke(provider=args.provider))

    if args.run_verify:
        checks.append(make_verify())

    total, failures, warnings = print_report(checks)
    print("\nSummary:")
    print(f"  Total checks: {total}")
    print(f"  Failures:     {failures}")
    print(f"  Warnings:     {warnings}")

    if failures:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
