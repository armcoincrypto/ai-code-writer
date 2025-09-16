import shutil

import dev_doctor as dd


def test_python_meets_requirement():
    assert dd.python_meets_requirement(3, 11)


def test_which_python_exists():
    assert shutil.which("python") or shutil.which("python3")


def test_has_module_sys():
    ok, _ = dd.has_module("sys")
    assert ok
