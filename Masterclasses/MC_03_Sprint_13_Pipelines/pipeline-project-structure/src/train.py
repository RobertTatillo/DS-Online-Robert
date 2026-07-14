"""
train.py — Entrena el pipeline completo y lo guarda en models/.

Uso (desde la raíz del repo):
    python src/train.py

Esto es lo que en una empresa correría un job programado (cron, Airflow,
GitHub Actions...) cada vez que hay datos nuevos o se quiere reentrenar.
"""

import time
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV

from pipeline import build_model_pipeline

DATA_PATH = "data/raw/titanic_train.csv"
MODEL_OUTPUT_PATH = "models/modelo_titanic.joblib"

# Grid reducido a propósito: en clase no queremos esperar minutos por un
# GridSearch completo. La sintaxis "modelo__param" es lo importante aquí,
# no la exhaustividad de la búsqueda.
PARAM_GRIDS = {
    "logistic": (
        LogisticRegression(random_state=42, max_iter=1000),
        {"modelo__C": [1, 10], "modelo__class_weight": ["balanced", None]},
    ),
    "random_forest": (
        RandomForestClassifier(random_state=42),
        {"modelo__n_estimators": [100], "modelo__max_depth": [4, 8]},
    ),
    "xgboost": (
        XGBClassifier(random_state=42, eval_metric="logloss"),
        {"modelo__n_estimators": [100], "modelo__max_depth": [3, 5]},
    ),
}


def main():
    print(f"Cargando datos de entrenamiento desde {DATA_PATH}...")
    train = pd.read_csv(DATA_PATH)
    y_train = train["Survived"]

    resultados = []
    mejores_modelos = {}

    for nombre, (estimator, param_grid) in PARAM_GRIDS.items():
        print(f"\nEntrenando {nombre}...")
        t0 = time.time()

        pipe = build_model_pipeline(estimator)
        grid = GridSearchCV(
            pipe, param_grid, cv=5, scoring="balanced_accuracy", n_jobs=-1
        )
        grid.fit(train, y_train)

        elapsed = time.time() - t0
        print(f"  -> best_score (CV): {grid.best_score_:.4f}  ({elapsed:.1f}s)")

        resultados.append((nombre, grid.best_score_))
        mejores_modelos[nombre] = grid.best_estimator_

    ganador = max(resultados, key=lambda x: x[1])[0]
    print(f"\nModelo ganador: {ganador}")

    joblib.dump(mejores_modelos[ganador], MODEL_OUTPUT_PATH)
    print(f"Modelo guardado en {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
