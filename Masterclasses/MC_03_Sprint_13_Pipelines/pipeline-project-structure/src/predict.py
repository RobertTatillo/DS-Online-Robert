"""
predict.py — Carga el modelo entrenado y predice sobre datos nuevos.

Uso (desde la raíz del repo):
    python src/predict.py

Fíjate en lo que este script NO hace: no importa pipeline.py, no reconstruye
ningún preprocesado, no sabe nada de imputaciones ni encodings. Solo carga
un .joblib y llama a .predict(). Todo el preprocesado viaja DENTRO del
artefacto guardado. Así es como un servicio de predicción real consume
un modelo — sin acoplarse al código de entrenamiento.
"""

import joblib
import pandas as pd
from sklearn.metrics import classification_report

DATA_PATH = "data/raw/titanic_test.csv"
MODEL_PATH = "models/modelo_titanic.joblib"


def main():
    print(f"Cargando modelo desde {MODEL_PATH}...")
    modelo = joblib.load(MODEL_PATH)

    print(f"Cargando datos nuevos desde {DATA_PATH}...")
    datos_nuevos = pd.read_csv(DATA_PATH)

    predicciones = modelo.predict(datos_nuevos)
    print("\nPrimeras 10 predicciones:", predicciones[:10])

    # En este caso de demo sí tenemos el target real para evaluar.
    # En producción, esto normalmente no existiría aquí.
    if "Survived" in datos_nuevos.columns:
        print("\nEvaluación contra el target real (solo posible en esta demo):")
        print(classification_report(datos_nuevos["Survived"], predicciones))


if __name__ == "__main__":
    main()
