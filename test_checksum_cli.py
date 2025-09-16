import hashlib
import pathlib
import subprocess
import sys
import tempfile


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=20)


def test_help_shows_expected_options():
    script = pathlib.Path(__file__).with_name("checksum_cli.py")
    cp = run([sys.executable, str(script), "--help"])
    assert cp.returncode == 0
    assert "--path" in cp.stdout
    assert "--algo" in cp.stdout
    assert "--dry-run" in cp.stdout
    assert "--debug-env" in cp.stdout


def test_dry_run_does_not_write():
    script = pathlib.Path(__file__).with_name("checksum_cli.py")
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / "sample.bin"
        out = pathlib.Path(td) / "digest.txt"
        f.write_bytes(b"hello world")
        cp = run(
            [
                sys.executable,
                str(script),
                "--path",
                str(f),
                "--out",
                str(out),
                "--dry-run",
            ]
        )
        assert cp.returncode == 0
        assert "Result:" in cp.stdout
        assert not out.exists()


def test_sha256_matches_python_hashlib():
    script = pathlib.Path(__file__).with_name("checksum_cli.py")
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / "data.bin"
        data = b"abc123"
        f.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        cp = run([sys.executable, str(script), "--path", str(f)])
        assert cp.returncode == 0
        out = cp.stdout.strip()
        assert "Result:" in out
        got = out.split("Result:", 1)[1].strip()
        assert got == expected
