"""
pipeline.py — Única fuente de verdad del preprocesado.

Todo el preprocesado (imputación, encoding, transformación de Fare, escalado)
vive AQUÍ y solo aquí. Ni train.py ni predict.py duplican esta lógica: la importan.

Esto es justo lo que un enfoque basado en funciones sueltas no garantiza —
si tuvieras una función en el notebook de entrenamiento y otra "equivalente"
en el script de predicción, nada te avisa cuando divergen.
"""

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer

# Columnas que no aportan señal para el modelo (identificadores, texto libre
# de alta cardinalidad, o con demasiados nulos para imputar con garantías)
COLUMNS_TO_EXCLUDE = ["PassengerId", "Name", "Cabin", "Ticket", "Survived"]


def build_preprocessing_pipeline() -> ColumnTransformer:
    """
    Construye el ColumnTransformer de preprocesado.

    Decisiones (ver notebook de la clase para el razonamiento completo):
    - Age: imputación por mediana (variable con outliers, no queremos que la
      media se desplace por ellos)
    - Fare: imputación por mediana + log1p (distribución con cola larga) + escalado
    - Sex, Embarked: imputación por moda + OneHotEncoder (pocas categorías)
    - Pclass, SibSp, Parch: se dejan tal cual (passthrough) porque son
      ordinales/discretas y un modelo basado en árboles no necesita escalado.
      OJO: si vas a usar LogisticRegression, Pclass como entero SIN escalar
      puede pesar más de lo debido frente al resto de variables — es una
      decisión consciente, no un descuido (coméntalo en clase).
    """
    cat_pipeline = Pipeline([
        ("imputar_moda", SimpleImputer(strategy="most_frequent")),
        ("one_hot", OneHotEncoder(drop="if_binary", handle_unknown="ignore")),
    ])

    fare_pipeline = Pipeline([
        ("imputar_mediana", SimpleImputer(strategy="median")),
        ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
        ("escalar", StandardScaler()),
    ])

    age_pipeline = Pipeline([
        ("imputar_mediana", SimpleImputer(strategy="median")),
        ("escalar", StandardScaler()),
    ])

    preprocessing = ColumnTransformer(
        [
            ("fare", fare_pipeline, ["Fare"]),
            ("age", age_pipeline, ["Age"]),
            ("categoricas", cat_pipeline, ["Sex", "Embarked"]),
            ("excluir", "drop", COLUMNS_TO_EXCLUDE),
        ],
        remainder="passthrough",
    )
    return preprocessing


def build_model_pipeline(model) -> Pipeline:
    """Envuelve cualquier estimador de sklearn con el preprocesado completo."""
    return Pipeline([
        ("preprocesado", build_preprocessing_pipeline()),
        ("modelo", model),
    ])
