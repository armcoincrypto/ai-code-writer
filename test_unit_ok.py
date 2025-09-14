import pathlib
import subprocess
import sys


def test_script_runs():
    script = pathlib.Path(__file__).with_name("unit_ok.py")
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=10
    )
    assert proc.returncode == 0
    assert "UNIT TEST OK" in proc.stdout
