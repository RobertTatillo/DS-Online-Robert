# Pipeline-Sklearn-demo

Ejemplo mínimo de cómo un modelo de sklearn construido con `Pipeline` pasa de
notebook de exploración a algo que se puede entrenar y servir como en una
empresa real.

## Estructura

```
titanic-pipeline-demo/
├── data/
│   ├── raw/              # Datos de entrada, tal como llegan (no se tocan)
│   └── processed/        # Datos intermedios si algún día hicieran falta
├── models/               # Modelos entrenados (.joblib) — NO se versiona en git
├── notebooks/            # Exploración, prototipado, EDA. Nunca código de producción
├── src/
│   ├── pipeline.py       # Única definición del preprocesado (fuente de verdad)
│   ├── train.py          # Entrena y guarda el modelo
│   └── predict.py        # Carga el modelo y predice sobre datos nuevos
├── requirements.txt
└── .gitignore
```

## Por qué esta estructura

- **`notebooks/` es solo para explorar.** Nada de lo que se despliega vive
  únicamente en un notebook. Un notebook no se puede programar en un cron,
  no se testea fácilmente y es fácil ejecutar celdas fuera de orden.
- **`src/pipeline.py` es la única fuente de verdad del preprocesado.**
  Tanto `train.py` como `predict.py` importan de aquí. Si mañana cambias
  cómo se imputa `Age`, lo cambias en un solo sitio y todo el repo queda
  consistente. Con funciones sueltas copiadas en varios notebooks, nada te
  avisa cuando dos versiones "equivalentes" empiezan a divergir.
- **`models/` no se versiona en git.** Los modelos son artefactos binarios
  que se generan a partir del código + los datos. En una empresa real esto
  se gestiona con algo como un model registry (MLflow, S3 + versionado,
  etc.) — aquí, por simplicidad, solo lo mantenemos fuera de git.
- **`predict.py` no sabe nada de preprocesado.** Solo hace
  `joblib.load(...)` y `.predict(...)`. Todo el preprocesado viaja dentro
  del pipeline serializado. Esto es lo que permite que un servicio de
  predicción (una API, un job batch, lo que sea) no tenga que importar el
  código de entrenamiento para funcionar.

## Cómo se usa

```bash
pip install -r requirements.txt

# Entrena y guarda el mejor modelo en models/modelo_titanic.joblib
python src/train.py

# Carga ese modelo y predice sobre datos nuevos
python src/predict.py
```

## Lo que esto NO es

**Esto es una versión mínima** . En un proyecto real
probablemente añadirías: tests (pytest), logging, configuración por YAML/env
vars en lugar de constantes hardcodeadas, versionado del propio dataset
(DVC), un model registry en condiciones, CI/CD, y probablemente Docker para
empaquetar el entorno. La estructura de carpetas, sin embargo, ya es
prácticamente la que verías en un repo profesional pequeño-mediano.
