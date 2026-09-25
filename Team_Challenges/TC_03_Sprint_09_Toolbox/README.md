# toolbox_ml 🧰

Paquete de Python con las funciones de análisis exploratorio que más se repiten en un
proyecto de Data Science: radiografiar un DataFrame, clasificar sus variables y
seleccionar — con criterio estadístico, no a ojo — qué columnas merecen entrar en un
modelo de regresión.

**Team Challenge del Sprint 9** · Bootcamp Data Science, The Bridge.

---

## Instalación

```bash
git clone https://github.com/RobertTatillo/toolbox_ml.git
cd toolbox_ml

python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt
pip install -e .
```

El `pip install -e .` instala el paquete en modo editable: se puede importar desde
cualquier notebook o script sin tocar el `PYTHONPATH`, y los cambios en el código se
reflejan al momento.

```python
from toolbox_ml.eda.core import describe_df, tipifica_variables
```

---

## Las funciones

Todas comparten el mismo contrato: **validan sus argumentos antes de hacer nada** y, si
algo está mal, imprimen el motivo concreto y devuelven `None` en lugar de lanzar una
excepción. Así un error de dedo no rompe la ejecución de un notebook.

### `describe_df(df)`

Una fila por columna del DataFrame con su tipo, porcentaje de nulos, valores únicos y
porcentaje de cardinalidad. Es la primera parada de cualquier EDA.

```python
>>> describe_df(titanic).head()
             tipo  porcentaje_nulos  valores_unicos  porcentaje_cardinalidad
survived    int64              0.00               2                     0.22
pclass      int64              0.00               3                     0.34
sex           str              0.00               2                     0.22
age       float64             19.87              88                     9.88
sibsp       int64              0.00               7                     0.79
```

### `tipifica_variables(df, umbral_categoria, umbral_continua)`

Sugiere el tipo de cada variable aplicando una cascada sobre su cardinalidad:

| Condición | Tipo sugerido |
|---|---|
| Cardinalidad `== 2` | `Binaria` |
| Cardinalidad `< umbral_categoria` | `Categórica` |
| Cardinalidad `>= umbral_categoria` y `%card >= umbral_continua` | `Numérica Continua` |
| Cardinalidad `>= umbral_categoria` y `%card < umbral_continua` | `Numérica Discreta` |

```python
>>> tipifica_variables(titanic, umbral_categoria=10, umbral_continua=15.0)
  nombre_variable      tipo_sugerido
0        survived            Binaria
1          pclass         Categórica
2             sex            Binaria
3             age  Numérica Discreta
6            fare  Numérica Continua
```

### `get_features_num_regression(df, target_col, umbral_corr, pvalue=None)`

Columnas numéricas cuya **correlación de Pearson** con el target supera `umbral_corr` en
valor absoluto, devueltas de mayor a menor correlación. Si se pasa `pvalue`, se exige
además que la correlación sea estadísticamente significativa a ese nivel.

```python
>>> get_features_num_regression(titanic, "fare", umbral_corr=0.2, pvalue=0.05)
['pclass', 'survived', 'parch']
```

### `plot_features_num_regression(df, target_col, columns=[], umbral_corr=0, pvalue=None)`

Misma selección, pero pintando un `pairplot`. Si hay más de 5 columnas las reparte en
varios pairplots (incluyendo siempre el target) para que sigan siendo legibles. Devuelve
la lista de columnas representadas.

### `get_features_cat_regression(df, target_col, pvalue=0.05)`

Columnas categóricas con relación estadísticamente significativa con el target.
**El test se elige solo** según la cardinalidad:

- **2 categorías** → test de **Mann-Whitney U** (compara las dos distribuciones)
- **más de 2** → **ANOVA de un factor** (compara las medias de todos los grupos)

```python
>>> get_features_cat_regression(titanic, "fare", pvalue=0.05)
['sex', 'embarked', 'class', 'who', 'adult_male', 'deck', 'embark_town', 'alive', 'alone']
```

### `plot_features_cat_regression(df, target_col, columns=[], pvalue=0.05, with_individual_plot=False)`

Histogramas del target agrupados por cada categoría que supera el test. Con
`with_individual_plot=True` cada variable genera su propia figura; con `False` (por
defecto) van todas en una rejilla de subplots.

### `detect_outliers(df, columns=[], metodo="iqr", umbral=1.5)` — *bonus*

Detecta atípicos por **IQR** o por **Z-score** y devuelve, por columna, cuántos hay, qué
porcentaje representan y en qué índices están.

```python
>>> detect_outliers(titanic, columns=["fare"], metodo="iqr")["fare"]
{'n_outliers': 116, 'porcentaje': 13.02, 'indices': [1, 27, 31, 34, ...]}
```

---

## Ejemplo completo

Del DataFrame crudo a la lista de features candidatas, en seis líneas:

```python
from toolbox_ml.eda.core import (
    describe_df, get_features_num_regression, get_features_cat_regression
)

num = get_features_num_regression(df, "fare", umbral_corr=0.2, pvalue=0.05)
cat = get_features_cat_regression(df, "fare", pvalue=0.05)

calidad = describe_df(df)
descartadas = calidad[calidad["porcentaje_nulos"] > 50].index.tolist()

features = [c for c in num + cat if c not in descartadas]
```

El notebook **`notebooks/demo.ipynb`** recorre las siete funciones sobre el Titanic con
todas las salidas visibles y comentadas.

---

## Tests

```bash
pytest tests/ -v
```

**30 tests, todos en verde.** Hay al menos tres por función, cubriendo los tres
escenarios que exige el enunciado:

- **Caso correcto** — input válido y output esperado
- **Caso límite** — DataFrame sin filas, columna constante, columna con todo nulos,
  más de 5 columnas para pintar, categórica de un solo nivel
- **Caso de error** — input inválido y la función devuelve `None`

```
======================= 30 passed in 7.04s ========================
```

---

## Estructura del repositorio

```
toolbox_ml/
├── __init__.py
└── eda/
    ├── __init__.py
    └── core.py              ← las 7 funciones
tests/
├── __init__.py
└── test_core.py             ← 30 tests
notebooks/
└── demo.ipynb               ← demostración sobre el Titanic
.gitignore
pytest.ini
README.md
requirements.txt
setup.py
```

---

## Decisiones de diseño

**Por qué devolver `None` en vez de lanzar una excepción.** El paquete está pensado para
usarse de forma interactiva en un notebook. Una excepción corta la ejecución de todas las
celdas siguientes; un `None` con un mensaje claro deja seguir trabajando. Es la misma
decisión que toman muchas utilidades de EDA.

**Por qué las validaciones están centralizadas.** Las mismas cuatro comprobaciones
(¿es un DataFrame?, ¿existe el target?, ¿es numérico?, ¿está el umbral en rango?) se
repiten en casi todas las funciones, así que viven en helpers privados
(`_es_dataframe`, `_target_valido`, `_es_float_en_rango`). Cambiar el mensaje de error de
un sitio los cambia en todos.

**Por qué las funciones `plot_*` reutilizan a las `get_*`.** La lógica estadística está
escrita una sola vez. `plot_features_num_regression` llama por dentro a
`get_features_num_regression` y se limita a dibujar lo que aquella selecciona, de modo que
las dos no pueden desincronizarse nunca.

**Por qué se excluye el target de la lista devuelta.** La correlación de una variable
consigo misma es 1 y superaría cualquier umbral. Devolverla sería un error silencioso muy
fácil de arrastrar hasta el modelo.

**Por qué los pairplots van en grupos de 4 + target.** El enunciado pide grupos de máximo
5 columnas. Como el target debe aparecer en todos los grupos, cada grupo lleva 4 features
más el target: 5 en total.

---

## Stack

Python 3.10+ · pandas · numpy · scipy · matplotlib · seaborn · pytest

---

## Autoría y flujo de trabajo Git

Paquete desarrollado **en solitario** por **Robert Matei**
([@RobertTatillo](https://github.com/RobertTatillo)): diseño de las funciones, tests,
notebook de demostración y documentación.

El enunciado plantea un reparto por integrante. Al trabajar solo, ese reparto se convirtió
en un **orden de construcción**, respetando el consejo del propio enunciado de acordar
primero el contrato de cada función y escribir los stubs y los tests antes que la
implementación:

| Fase | Rama | Qué entró |
|---|---|---|
| 1 | `feature/setup` | `setup.py`, `__init__.py`, estructura del paquete |
| 2 | `feature/describe-tipifica` | `describe_df`, `tipifica_variables` y sus tests |
| 3 | `feature/num-regression` | `get/plot_features_num_regression` y sus tests |
| 4 | `feature/cat-regression` | `get/plot_features_cat_regression` y sus tests |
| 5 | `feature/bonus` | `detect_outliers` y sus tests |
| 6 | `feature/demo-docs` | `notebooks/demo.ipynb` y este README |

Commits con **Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`) y merge con
**Squash and merge** sobre una `main` protegida.

**Lo que más se notó al trabajar solo:** escribir los tests antes que la implementación deja
de ser una forma de paralelizar el trabajo entre dos personas y pasa a ser una forma de
**fijar el contrato de la función antes de tener prisa por que funcione**. Varias de las
comprobaciones de entrada del paquete salieron de escribir primero el test del caso de error.
