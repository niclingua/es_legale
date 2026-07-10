"""API REST per la classificazione dei fiori Iris.

Espone due endpoint:
  - GET  /         → stato del servizio (health check)
  - POST /predict  → predizione della specie a partire dalle 4 feature

Il modello viene caricato una sola volta all'avvio del processo.
"""
import os

import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field

MODEL_PATH = os.environ.get("MODEL_PATH", "model.joblib")
CLASS_NAMES = ["setosa", "versicolor", "virginica"]

app = FastAPI(title="Iris Classifier API", version="1.0.0")

# Caricato una sola volta all'avvio → latenza minima per richiesta.
model = joblib.load(MODEL_PATH)


class IrisFeatures(BaseModel):
    sepal_length: float = Field(..., ge=0)
    sepal_width: float = Field(..., ge=0)
    petal_length: float = Field(..., ge=0)
    petal_width: float = Field(..., ge=0)


@app.get("/")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict")
def predict(features: IrisFeatures):
    x = np.array(
        [
            [
                features.sepal_length,
                features.sepal_width,
                features.petal_length,
                features.petal_width,
            ]
        ]
    )
    idx = int(model.predict(x)[0])
    return {"class_id": idx, "class_name": CLASS_NAMES[idx]}
