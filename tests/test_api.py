"""Test dell'API con il TestClient di FastAPI.

Richiedono che `model.joblib` sia stato generato (`python train.py`).
"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root_serves_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Iris Classifier" in r.text


def test_health():
    r = client.get("/health")
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


def test_predict_versicolor():
    r = client.post(
        "/predict",
        json={
            "sepal_length": 6.0,
            "sepal_width": 2.7,
            "petal_length": 4.2,
            "petal_width": 1.3,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["class_id"] == 1
    assert body["class_name"] == "versicolor"


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


def test_predict_output_is_consistent():
    # class_id sempre in {0,1,2} e coerente con class_name.
    class_map = {0: "setosa", 1: "versicolor", 2: "virginica"}
    r = client.post(
        "/predict",
        json={
            "sepal_length": 5.9,
            "sepal_width": 3.0,
            "petal_length": 5.1,
            "petal_width": 1.8,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["class_id"] in class_map
    assert body["class_name"] == class_map[body["class_id"]]


def test_predict_missing_field():
    # Feature mancanti → 422 di validazione Pydantic.
    r = client.post("/predict", json={"sepal_length": 5.1})
    assert r.status_code == 422


def test_predict_negative_value():
    # Valore negativo viola Field(ge=0) → 422.
    r = client.post(
        "/predict",
        json={
            "sepal_length": -1.0,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        },
    )
    assert r.status_code == 422
