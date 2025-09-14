import csv
import pathlib
import subprocess
import sys
import tempfile


def test_script_runs():
    script = pathlib.Path(__file__).with_name("stats_csv.py")
    with tempfile.TemporaryDirectory() as td:
        path = pathlib.Path(td) / "d.csv"
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["value"])
            w.writeheader()
            w.writerows([{"value": 1}, {"value": 2}, {"value": 3}])
        proc = subprocess.run(
            [sys.executable, str(script), str(path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0
    assert "mean" in proc.stdout
