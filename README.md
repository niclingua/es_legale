# Iris Classifier API

[![CI](https://github.com/niclingua/es_legale/actions/workflows/ci.yml/badge.svg)](https://github.com/niclingua/es_legale/actions/workflows/ci.yml)

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

> **CI** — ad ogni push e pull request verso `main`, GitHub Actions
> (`.github/workflows/ci.yml`) esegue automaticamente i test e una build Docker di verifica.
> Lo stato è mostrato dal badge in cima a questo README.

## Deploy su Google Cloud Run

Cloud Run esegue **un'immagine** (non `docker compose`): dal `Dockerfile` presente costruisce
l'immagine e la pubblica su un URL pubblico.

### Prerequisiti
1. Installare **Google Cloud SDK** → `gcloud --version`.
2. Autenticarsi: `gcloud auth login`.
3. Avere un **progetto GCP** con billing attivo e la **Cloud Run API** abilitata.

### Deploy (script incluso)
È disponibile `deploy.sh` che incapsula i comandi:

```bash
PROJECT_ID=mio-progetto REGION=europe-west1 ./deploy.sh
```

Oppure manualmente:

```bash
gcloud config set project <PROJECT_ID>
gcloud run deploy iris-api --source . --region <REGIONE> --allow-unauthenticated --port 8000
```

Al termine viene stampato l'**URL pubblico** del servizio.

> **Note importanti**
> - Il container ascolta su `0.0.0.0:${PORT}`: `PORT` è gestita dalla piattaforma, **non
>   impostarla come variabile a mano**.
> - Il filesystem su Cloud Run è **effimero**: il volume del `compose.yaml` vale solo in locale.
> - `--allow-unauthenticated` rende l'endpoint pubblico (necessario per la consegna).
> - Verifica il **free tier** corrente sulla pagina prezzi di Cloud Run; lo scale-to-zero
>   (default) evita addebiti da idle.

### Prova post-deploy
```bash
curl -X POST <URL_PUBBLICO>/predict -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

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
├── deploy.sh          # script di deploy su Cloud Run
├── .dockerignore
├── .gcloudignore      # esclusioni per il deploy da sorgente
├── .gitignore
├── .github/workflows/ci.yml  # CI: pytest + docker build
├── tests/test_api.py  # test degli endpoint
└── context.txt        # documento di progettazione tecnica
```
