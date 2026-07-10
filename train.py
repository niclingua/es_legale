"""Addestramento del classificatore Iris.

Carica il dataset Iris (built-in in scikit-learn), addestra una
LogisticRegression deterministica e salva l'artefatto `model.joblib`.
Il path di output è configurabile via variabile d'ambiente MODEL_PATH.
"""
import os

import joblib
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

MODEL_PATH = os.environ.get("MODEL_PATH", "model.joblib")


def main() -> None:
    X, y = load_iris(return_X_y=True)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_tr, y_tr)

    acc = accuracy_score(y_te, model.predict(X_te))
    print(f"Test accuracy: {acc:.3f}")

    joblib.dump(model, MODEL_PATH)
    print(f"Modello salvato in {MODEL_PATH}")


if __name__ == "__main__":
    main()
