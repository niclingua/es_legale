#!/usr/bin/env bash
#
# Deploy dell'Iris Classifier API su Google Cloud Run.
#
# Prerequisiti:
#   - Google Cloud SDK installato ($ gcloud --version)
#   - Autenticazione:      gcloud auth login
#   - Un progetto GCP con billing attivo e Cloud Run API abilitata
#
# Uso:
#   PROJECT_ID=mio-progetto REGION=europe-west1 ./deploy.sh
#
# Cloud Run costruisce l'immagine dal Dockerfile presente (deploy "da sorgente")
# e pubblica un URL. NON impostare la variabile PORT: la inietta la piattaforma.

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-<PROJECT_ID>}"
REGION="${REGION:-europe-west1}"
SERVICE="${SERVICE:-iris-api}"

if [[ "$PROJECT_ID" == "<PROJECT_ID>" ]]; then
  echo "ERRORE: imposta PROJECT_ID (es: PROJECT_ID=mio-progetto REGION=europe-west1 ./deploy.sh)" >&2
  exit 1
fi

echo ">> Progetto:  $PROJECT_ID"
echo ">> Regione:   $REGION"
echo ">> Servizio:  $SERVICE"

gcloud config set project "$PROJECT_ID"

gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8000

echo ">> Deploy completato. URL pubblico:"
gcloud run services describe "$SERVICE" \
  --region "$REGION" \
  --format 'value(status.url)'
