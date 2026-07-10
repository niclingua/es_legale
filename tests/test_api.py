"""Test dell'API con il TestClient di FastAPI.

Richiedono che `model.joblib` sia stato generato (`python train.py`).
"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_predict_setosa():
    r = client.post(
        "/predict",
        json={
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["class_id"] == 0
    assert body["class_name"] == "setosa"


def test_predict_virginica():
    r = client.post(
        "/predict",
        json={
            "sepal_length": 6.7,
            "sepal_width": 3.0,
            "petal_length": 5.2,
            "petal_width": 2.3,
        },
    )
    assert r.status_code == 200
    assert r.json()["class_name"] == "virginica"


def test_predict_invalid_input():
    # Feature mancanti → 422 di validazione Pydantic.
    r = client.post("/predict", json={"sepal_length": 5.1})
    assert r.status_code == 422
