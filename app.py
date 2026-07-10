"""API REST + mini web-app per la classificazione dei fiori Iris.

Endpoint:
  - GET  /         → mini web-app (pagina HTML con form di predizione)
  - GET  /health   → stato del servizio (health check, JSON)
  - POST /predict  → predizione della specie a partire dalle 4 feature

Il modello viene caricato una sola volta all'avvio del processo.
"""
import os

import joblib
import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

MODEL_PATH = os.environ.get("MODEL_PATH", "model.joblib")
CLASS_NAMES = ["setosa", "versicolor", "virginica"]

app = FastAPI(title="Iris Classifier API", version="1.1.0")

# Caricato una sola volta all'avvio → latenza minima per richiesta.
model = joblib.load(MODEL_PATH)


class IrisFeatures(BaseModel):
    sepal_length: float = Field(..., ge=0)
    sepal_width: float = Field(..., ge=0)
    petal_length: float = Field(..., ge=0)
    petal_width: float = Field(..., ge=0)


@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_HTML


@app.get("/health")
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


# --- Mini web-app servita su "/" ------------------------------------------------
INDEX_HTML = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Iris Classifier</title>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    margin: 0; min-height: 100vh; display: flex; align-items: center;
    justify-content: center; padding: 24px;
    background: linear-gradient(135deg, #6d5efc 0%, #46b3e6 100%); color: #1f2937;
  }
  .card {
    background: #fff; border-radius: 16px; box-shadow: 0 20px 50px rgba(0,0,0,.25);
    width: 100%; max-width: 440px; padding: 28px 28px 24px;
  }
  h1 { margin: 0 0 4px; font-size: 1.5rem; }
  .sub { margin: 0 0 20px; color: #6b7280; font-size: .9rem; }
  label { display: block; font-size: .85rem; font-weight: 600; margin: 12px 0 4px; }
  input {
    width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px;
    font-size: 1rem;
  }
  input:focus { outline: none; border-color: #6d5efc; box-shadow: 0 0 0 3px rgba(109,94,252,.2); }
  .row { display: flex; gap: 12px; }
  .row > div { flex: 1; }
  button {
    width: 100%; margin-top: 20px; padding: 12px; border: 0; border-radius: 8px;
    background: #6d5efc; color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer;
  }
  button:hover { background: #5b4de0; }
  button:disabled { opacity: .6; cursor: default; }
  .result {
    margin-top: 20px; padding: 16px; border-radius: 10px; text-align: center;
    font-size: 1.1rem; display: none;
  }
  .result.show { display: block; }
  .result .name { font-size: 1.6rem; font-weight: 700; text-transform: capitalize; }
  .setosa { background: #eef2ff; color: #4338ca; }
  .versicolor { background: #ecfdf5; color: #047857; }
  .virginica { background: #fef2f2; color: #b91c1c; }
  .error { background: #fef2f2; color: #b91c1c; }
  .foot { margin-top: 18px; text-align: center; font-size: .8rem; color: #9ca3af; }
  .foot a { color: #6d5efc; text-decoration: none; }
</style>
</head>
<body>
  <div class="card">
    <h1>🌸 Iris Classifier</h1>
    <p class="sub">Inserisci le 4 misure del fiore (in cm) e scopri la specie.</p>
    <form id="f">
      <div class="row">
        <div>
          <label>Sepalo — lunghezza</label>
          <input type="number" step="0.1" min="0" id="sepal_length" value="5.1" required>
        </div>
        <div>
          <label>Sepalo — larghezza</label>
          <input type="number" step="0.1" min="0" id="sepal_width" value="3.5" required>
        </div>
      </div>
      <div class="row">
        <div>
          <label>Petalo — lunghezza</label>
          <input type="number" step="0.1" min="0" id="petal_length" value="1.4" required>
        </div>
        <div>
          <label>Petalo — larghezza</label>
          <input type="number" step="0.1" min="0" id="petal_width" value="0.2" required>
        </div>
      </div>
      <button type="submit" id="btn">Predici specie</button>
    </form>
    <div class="result" id="res"></div>
    <p class="foot">API REST · <a href="/docs">documentazione /docs</a></p>
  </div>

<script>
const f = document.getElementById('f');
const res = document.getElementById('res');
const btn = document.getElementById('btn');

f.addEventListener('submit', async (e) => {
  e.preventDefault();
  btn.disabled = true; btn.textContent = 'Calcolo...';
  res.className = 'result';
  const payload = {
    sepal_length: parseFloat(document.getElementById('sepal_length').value),
    sepal_width:  parseFloat(document.getElementById('sepal_width').value),
    petal_length: parseFloat(document.getElementById('petal_length').value),
    petal_width:  parseFloat(document.getElementById('petal_width').value),
  };
  try {
    const r = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error('Richiesta non valida (' + r.status + ')');
    const data = await r.json();
    res.className = 'result show ' + data.class_name;
    res.innerHTML = 'Specie prevista:<div class="name">' + data.class_name + '</div>'
                  + '<small>class_id: ' + data.class_id + '</small>';
  } catch (err) {
    res.className = 'result show error';
    res.textContent = '⚠️ ' + err.message;
  } finally {
    btn.disabled = false; btn.textContent = 'Predici specie';
  }
});
</script>
</body>
</html>
"""
