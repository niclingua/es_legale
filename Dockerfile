FROM python:3.12-slim

# 1) Impostazioni Python pulite
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/model.joblib \
    PORT=8000

WORKDIR /app

# 2) Dipendenze PRIMA del codice → sfrutta la cache dei layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Codice sorgente
COPY train.py app.py ./

# 4) Addestramento al build → model.joblib finisce nell'immagine
RUN python train.py

# 5) Utente non-root (sicurezza)
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# 6) Avvio: ascolta sulla porta iniettata (Cloud Run) o 8000 in locale
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
