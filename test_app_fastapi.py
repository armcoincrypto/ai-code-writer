import pathlib
import shlex
import subprocess
import sys

TEST_ARGS = "--help"


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, timeout=30)


def test_script_runs_ok() -> None:
    script = pathlib.Path(__file__).with_name("app_fastapi.py")
    args = [sys.executable, str(script)]
    if TEST_ARGS:
        args += shlex.split(TEST_ARGS)
    cp = _run(args)
    assert cp.returncode == 0, cp.stderr
