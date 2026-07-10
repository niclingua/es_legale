# Iris Classifier API

Servizio REST che classifica i fiori **Iris** (setosa / versicolor / virginica) a partire
dalle 4 misure del fiore. Il modello (scikit-learn `LogisticRegression`) viene **addestrato
durante la build dell'immagine** e servito da **FastAPI**; il tutto è containerizzato con
**Docker** e orchestrato in locale con **Docker Compose**.

## Architettura

```
CLIENT (curl / browser)
        │ HTTP (REST/JSON)
        ▼
FastAPI app (app.py)
  GET  /         → health / stato
  POST /predict  → validazione Pydantic → model.predict()
        │ carica all'avvio
        ▼
model.joblib  (prodotto da train.py durante la build)
```

Principio guida: **separazione training / serving**. `train.py` produce l'artefatto
`model.joblib`; `app.py` lo carica **una sola volta all'avvio** e non riaddestra mai a runtime.

## Prerequisiti

- Docker + Docker Compose (`docker compose version`)
- (opzionale, per sviluppo senza Docker) Python 3.12+

## Avvio rapido (un solo comando)

```bash
docker compose up --build
```

L'API sarà disponibile su `http://localhost:8000`.
Documentazione interattiva Swagger: `http://localhost:8000/docs`.

## Esempi d'uso

Stato del servizio:

```bash
curl http://localhost:8000/
# {"status":"ok","model_loaded":true}
```

Predizione:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
# {"class_id":0,"class_name":"setosa"}

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":6.7,"sepal_width":3.0,"petal_length":5.2,"petal_width":2.3}'
# {"class_id":2,"class_name":"virginica"}
```

Input malformati (feature mancanti o negative) → risposta **422** automatica di Pydantic.

## Come viene generato `model.joblib`

`train.py` carica il dataset Iris (built-in in scikit-learn), addestra una
`LogisticRegression(max_iter=1000, random_state=42)` — quindi **deterministica e
riproducibile** — e salva il modello con `joblib`. Nel `Dockerfile` questo avviene con
`RUN python train.py`, così il modello finisce **dentro l'immagine** (deploy autoconsistente).
Il file è committato nel repo per praticità di consegna, ma può essere rigenerato in qualsiasi
momento con `python train.py`.

## Variabili d'ambiente

| Variabile | Default | Uso |
|-----------|---------|-----|
| `MODEL_PATH` | `model.joblib` | Path dell'artefatto letto/scritto da `train.py` e `app.py` |
| `PORT` | `8000` | Porta di ascolto di Uvicorn (Cloud Run la inietta, tipicamente 8080) |
| `APP_ENV` | `local` | Ambiente logico (impostata in `compose.yaml`) |

## Sviluppo locale senza Docker

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python train.py
uvicorn app:app --port 8000
pytest        # esegue tests/test_api.py
```

## Deploy su Google Cloud Run

Cloud Run esegue **un'immagine** (non `docker compose`). Deploy da sorgente:

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud run deploy iris-api --source . --region <REGIONE> --allow-unauthenticated
```

> Il container ascolta su `0.0.0.0:${PORT}`: `PORT` è iniettata da Cloud Run, **non va
> impostata manualmente**. Il filesystem su Cloud Run è effimero (il volume del compose vale
> solo in locale).

**URL pubblico del deploy:** _(da inserire dopo il deploy)_

## Sicurezza

- Il container gira come utente **non-root** (`appuser`).
- **Nessuna credenziale, password o chiave** è presente nel repository né nella sua history.
  Eventuali segreti andrebbero gestiti con `.env` (in `.gitignore`) in locale e con Secret
  Manager / variabili d'ambiente della piattaforma in cloud.

## Struttura del progetto

```
.
├── app.py             # API FastAPI
├── train.py           # addestramento → model.joblib
├── model.joblib       # modello serializzato (committato)
├── requirements.txt   # dipendenze con versioni pinnate
├── Dockerfile         # build: install → train → serve (non-root)
├── compose.yaml       # orchestrazione locale (porta, env, volume)
├── .dockerignore
├── .gitignore
├── tests/test_api.py  # test degli endpoint
└── context.txt        # documento di progettazione tecnica
```
