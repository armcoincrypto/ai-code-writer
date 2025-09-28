from fastapi.testclient import TestClient

from app_fastapi import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_sum_ok():
    r = client.get("/sum", params={"a": 2.5, "b": 7.5})
    assert r.status_code == 200
    assert r.json() == {"result": 10.0}


def test_sum_reject_nan():
    r = client.get("/sum", params={"a": "nan", "b": 1})
    assert r.status_code == 400
    assert "Result not finite" in r.json().get("detail", "")
