"""
Funciones de análisis exploratorio del paquete toolbox_ml.

Todas las funciones siguen el mismo contrato: validan sus argumentos antes de
hacer nada y, si alguna comprobación falla, imprimen el motivo por pantalla y
devuelven None en lugar de lanzar una excepción. Así el paquete se puede usar de
forma interactiva en un notebook sin que un error tonto rompa la ejecución.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

__all__ = [
    "describe_df",
    "tipifica_variables",
    "get_features_num_regression",
    "plot_features_num_regression",
    "get_features_cat_regression",
    "plot_features_cat_regression",
    "detect_outliers",
]


# ---------------------------------------------------------------------------
# Validaciones internas
#
# Se repiten en casi todas las funciones públicas, así que viven en helpers
# privados. Cada uno devuelve True si todo está bien y, si no, imprime el motivo
# concreto del fallo y devuelve False.
# ---------------------------------------------------------------------------

def _es_dataframe(df) -> bool:
    """Comprueba que el argumento sea un DataFrame de pandas no vacío."""
    if not isinstance(df, pd.DataFrame):
        print(f"Error: se esperaba un pd.DataFrame y se recibió {type(df).__name__}.")
        return False
    if df.shape[1] == 0:
        print("Error: el DataFrame no tiene ninguna columna.")
        return False
    return True


def _es_float_en_rango(valor, nombre: str, minimo: float, maximo: float) -> bool:
    """Comprueba que `valor` sea un número real dentro del intervalo [minimo, maximo]."""
    # bool es subclase de int en Python, así que hay que excluirlo explícitamente
    if isinstance(valor, bool) or not isinstance(valor, (int, float, np.integer, np.floating)):
        print(f"Error: '{nombre}' debe ser un número, y se recibió {type(valor).__name__}.")
        return False
    if not (minimo <= float(valor) <= maximo):
        print(f"Error: '{nombre}' debe estar entre {minimo} y {maximo}, y vale {valor}.")
        return False
    return True


def _target_valido(df: pd.DataFrame, target_col: str) -> bool:
    """Comprueba que `target_col` exista en el DataFrame y sea numérica."""
    if not isinstance(target_col, str) or target_col == "":
        print("Error: 'target_col' debe ser el nombre (str) de una columna.")
        return False
    if target_col not in df.columns:
        print(f"Error: la columna '{target_col}' no existe en el DataFrame.")
        return False
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        print(f"Error: la columna '{target_col}' debe ser numérica para un problema de regresión.")
        return False
    return True


# ---------------------------------------------------------------------------
# describe_df
# ---------------------------------------------------------------------------

def describe_df(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Genera un resumen estadístico descriptivo de un DataFrame.

    Argumentos:
        df (pd.DataFrame): DataFrame a analizar.

    Retorna:
        pd.DataFrame: DataFrame con una fila por cada columna del input, indexado
        por el nombre de esa columna, y con las columnas: 'tipo',
        'porcentaje_nulos', 'valores_unicos' y 'porcentaje_cardinalidad'.
        Retorna None si el input no es un DataFrame válido.
    """
    if not _es_dataframe(df):
        return None

    n_filas = len(df)

    # Con 0 filas los porcentajes serían una división por cero: devuelve 0.0
    if n_filas == 0:
        porcentaje_nulos = pd.Series(0.0, index=df.columns)
        porcentaje_cardinalidad = pd.Series(0.0, index=df.columns)
    else:
        porcentaje_nulos = (df.isna().sum() / n_filas * 100).round(2)
        porcentaje_cardinalidad = (df.nunique() / n_filas * 100).round(2)

    resumen = pd.DataFrame({
        "tipo": df.dtypes.astype(str),
        "porcentaje_nulos": porcentaje_nulos,
        "valores_unicos": df.nunique(),
        "porcentaje_cardinalidad": porcentaje_cardinalidad,
    })
    resumen.index.name = None
    return resumen


# ---------------------------------------------------------------------------
# tipifica_variables
# ---------------------------------------------------------------------------

def tipifica_variables(
    df: pd.DataFrame,
    umbral_categoria: int,
    umbral_continua: float,
) -> Optional[pd.DataFrame]:
    """
    Sugiere el tipo de cada variable del DataFrame a partir de su cardinalidad.

    La lógica es una cascada de cuatro casos:
      - cardinalidad == 2                                        -> 'Binaria'
      - cardinalidad < umbral_categoria                          -> 'Categórica'
      - cardinalidad >= umbral_categoria y %card >= umbral_continua -> 'Numérica Continua'
      - cardinalidad >= umbral_categoria y %card <  umbral_continua -> 'Numérica Discreta'

    Argumentos:
        df (pd.DataFrame): DataFrame a analizar.
        umbral_categoria (int): número de valores únicos por debajo del cual una
            variable se considera categórica. Debe ser un entero positivo.
        umbral_continua (float): porcentaje de cardinalidad (0-100) a partir del
            cual una variable numérica se considera continua.

    Retorna:
        pd.DataFrame: DataFrame con las columnas 'nombre_variable' y
        'tipo_sugerido', con una fila por columna del input.
        Retorna None si alguna comprobación de entrada falla.
    """
    if not _es_dataframe(df):
        return None

    # umbral_categoria: entero estricto y positivo (bool queda excluido)
    if isinstance(umbral_categoria, bool) or not isinstance(umbral_categoria, (int, np.integer)):
        print(f"Error: 'umbral_categoria' debe ser un entero, y se recibió {type(umbral_categoria).__name__}.")
        return None
    if umbral_categoria <= 0:
        print(f"Error: 'umbral_categoria' debe ser positivo, y vale {umbral_categoria}.")
        return None

    if not _es_float_en_rango(umbral_continua, "umbral_continua", 0, 100):
        return None

    n_filas = len(df)
    filas = []

    for col in df.columns:
        cardinalidad = df[col].nunique()
        # con 0 filas no hay porcentaje posible: queda en 0
        pct_cardinalidad = (cardinalidad / n_filas * 100) if n_filas else 0.0

        if cardinalidad == 2:
            tipo = "Binaria"
        elif cardinalidad < umbral_categoria:
            tipo = "Categórica"
        elif pct_cardinalidad >= umbral_continua:
            tipo = "Numérica Continua"
        else:
            tipo = "Numérica Discreta"

        filas.append({"nombre_variable": col, "tipo_sugerido": tipo})

    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# get_features_num_regression
# ---------------------------------------------------------------------------

def get_features_num_regression(
    df: pd.DataFrame,
    target_col: str,
    umbral_corr: float,
    pvalue: float = None,
) -> Optional[list]:
    """
    Selecciona las columnas numéricas más correlacionadas con el target.

    Devuelve las columnas cuya correlación de Pearson con `target_col` supere en
    valor absoluto `umbral_corr`. Si `pvalue` no es None, aplica además un filtro
    de significación estadística: solo se devuelven las columnas cuyo test de
    correlación tenga un p-valor menor que `pvalue`.

    Argumentos:
        df (pd.DataFrame): DataFrame a analizar.
        target_col (str): nombre de la columna objetivo. Debe ser numérica.
        umbral_corr (float): umbral de correlación en valor absoluto, entre 0 y 1.
        pvalue (float, opcional): nivel de significación entre 0 y 1. Si es None
            (valor por defecto) no se aplica el filtro estadístico.

    Retorna:
        list: nombres de las columnas numéricas que cumplen los criterios,
        ordenadas de mayor a menor correlación absoluta con el target.
        Retorna None si alguna comprobación de entrada falla.
    """
    if not _es_dataframe(df):
        return None
    if not _target_valido(df, target_col):
        return None
    if not _es_float_en_rango(umbral_corr, "umbral_corr", 0, 1):
        return None
    if pvalue is not None and not _es_float_en_rango(pvalue, "pvalue", 0, 1):
        return None

    candidatas = [
        col for col in df.select_dtypes(include=np.number).columns
        if col != target_col
    ]

    seleccionadas = []
    for col in candidatas:
        # pearsonr no admite nulos: solo entran las filas en las que target
        # y columna tienen valor a la vez
        pareja = df[[target_col, col]].dropna()

        # el test necesita al menos 3 puntos y que ninguna serie sea constante
        if len(pareja) < 3 or pareja[col].nunique() < 2 or pareja[target_col].nunique() < 2:
            continue

        corr, p = stats.pearsonr(pareja[col], pareja[target_col])

        if abs(corr) <= umbral_corr:
            continue
        if pvalue is not None and p >= pvalue:
            continue

        seleccionadas.append((col, abs(corr)))

    # de mayor a menor correlación absoluta, para que la lista sea informativa
    seleccionadas.sort(key=lambda par: par[1], reverse=True)
    return [col for col, _ in seleccionadas]


# ---------------------------------------------------------------------------
# plot_features_num_regression
# ---------------------------------------------------------------------------

def plot_features_num_regression(
    df: pd.DataFrame,
    target_col: str = "",
    columns: list = [],
    umbral_corr: float = 0,
    pvalue: float = None,
) -> Optional[list]:
    """
    Pinta pairplots del target contra las columnas numéricas que superan los
    criterios de correlación de `get_features_num_regression`.

    Si la lista de columnas a representar supera los 5 elementos, se divide en
    grupos de 5 como máximo y se pinta un pairplot por grupo, incluyendo siempre
    el target en cada uno.

    Argumentos:
        df (pd.DataFrame): DataFrame a analizar.
        target_col (str): nombre de la columna objetivo. Debe ser numérica.
        columns (list): columnas candidatas. Si está vacía se usan todas las
            columnas numéricas del DataFrame.
        umbral_corr (float): umbral de correlación en valor absoluto, entre 0 y 1.
        pvalue (float, opcional): nivel de significación entre 0 y 1.

    Retorna:
        list: columnas que han superado los criterios y se han representado.
        Retorna None si alguna comprobación de entrada falla.
    """
    if not _es_dataframe(df):
        return None
    if not _target_valido(df, target_col):
        return None
    if not _es_float_en_rango(umbral_corr, "umbral_corr", 0, 1):
        return None
    if pvalue is not None and not _es_float_en_rango(pvalue, "pvalue", 0, 1):
        return None
    if not isinstance(columns, list):
        print(f"Error: 'columns' debe ser una lista, y se recibió {type(columns).__name__}.")
        return None

    # Reutiliza la función de selección para no duplicar la lógica estadística
    candidatas = get_features_num_regression(df, target_col, umbral_corr, pvalue)
    if candidatas is None:
        return None

    # Si el usuario pasó una lista concreta, solo vale la intersección
    if columns:
        inexistentes = [c for c in columns if c not in df.columns]
        if inexistentes:
            print(f"Error: estas columnas no existen en el DataFrame: {inexistentes}.")
            return None
        candidatas = [c for c in candidatas if c in columns]

    if not candidatas:
        print("Ninguna columna supera los criterios indicados: no hay nada que pintar.")
        return []

    # Grupos de 4 features + el target = 5 columnas por pairplot como máximo
    TAM_GRUPO = 4
    for inicio in range(0, len(candidatas), TAM_GRUPO):
        grupo = candidatas[inicio:inicio + TAM_GRUPO]
        sns.pairplot(df[[target_col] + grupo].dropna())
        plt.suptitle(f"{target_col} vs {', '.join(grupo)}", y=1.02)
        plt.show()

    return candidatas


# ---------------------------------------------------------------------------
# get_features_cat_regression
# ---------------------------------------------------------------------------

def get_features_cat_regression(
    df: pd.DataFrame,
    target_col: str,
    pvalue: float = 0.05,
) -> Optional[list]:
    """
    Selecciona las columnas categóricas relacionadas significativamente con el target.

    El test estadístico se elige automáticamente según la cardinalidad de cada
    variable categórica:
      - exactamente 2 categorías -> test de Mann-Whitney U (scipy.stats.mannwhitneyu)
      - más de 2 categorías      -> ANOVA de un factor (scipy.stats.f_oneway)

    En ambos casos, si el p-valor resultante es menor que `pvalue`, se considera
    que la variable tiene relación significativa con el target.

    Argumentos:
        df (pd.DataFrame): DataFrame a analizar.
        target_col (str): nombre de la columna objetivo. Debe ser numérica.
        pvalue (float): nivel de significación entre 0 y 1. Por defecto 0.05.

    Retorna:
        list: nombres de las columnas categóricas que superan el test.
        Retorna None si alguna comprobación de entrada falla.
    """
    if not _es_dataframe(df):
        return None
    if not _target_valido(df, target_col):
        return None
    if not _es_float_en_rango(pvalue, "pvalue", 0, 1):
        return None

    # Cuentan como categóricas las de tipo object, category o bool
    candidatas = [
        col for col in df.columns
        if col != target_col
        and (pd.api.types.is_object_dtype(df[col])
             or isinstance(df[col].dtype, pd.CategoricalDtype)
             or pd.api.types.is_bool_dtype(df[col])
             or pd.api.types.is_string_dtype(df[col]))
    ]

    seleccionadas = []
    for col in candidatas:
        pareja = df[[target_col, col]].dropna()
        if pareja.empty:
            continue

        # una lista con los valores del target para cada categoría
        grupos = [
            grupo[target_col].values
            for _, grupo in pareja.groupby(col, observed=True)
            if len(grupo) >= 2  # los tests necesitan al menos 2 observaciones por grupo
        ]
        if len(grupos) < 2:
            continue

        try:
            if len(grupos) == 2:
                # dos categorías: compara las dos distribuciones
                _, p = stats.mannwhitneyu(grupos[0], grupos[1], alternative="two-sided")
            else:
                # más de dos: compara las medias de todos los grupos a la vez
                _, p = stats.f_oneway(*grupos)
        except ValueError:
            # p. ej. si todos los valores del target son idénticos en un grupo
            continue

        if not np.isnan(p) and p < pvalue:
            seleccionadas.append(col)

    return seleccionadas


# ---------------------------------------------------------------------------
# plot_features_cat_regression
# ---------------------------------------------------------------------------

def plot_features_cat_regression(
    df: pd.DataFrame,
    target_col: str = "",
    columns: list = [],
    pvalue: float = 0.05,
    with_individual_plot: bool = False,
) -> Optional[list]:
    """
    Pinta histogramas del target agrupados por cada variable categórica que
    supera el test estadístico de `get_features_cat_regression`.

    Argumentos:
        df (pd.DataFrame): DataFrame a analizar.
        target_col (str): nombre de la columna objetivo. Debe ser numérica.
        columns (list): columnas categóricas candidatas. Si está vacía se usan
            todas las categóricas del DataFrame.
        pvalue (float): nivel de significación entre 0 y 1. Por defecto 0.05.
        with_individual_plot (bool): si es True, cada variable genera su propia
            figura. Si es False (por defecto), todas van en una figura con subplots.

    Retorna:
        list: columnas categóricas que han superado el test y se han representado.
        Retorna None si alguna comprobación de entrada falla.
    """
    if not _es_dataframe(df):
        return None
    if not _target_valido(df, target_col):
        return None
    if not _es_float_en_rango(pvalue, "pvalue", 0, 1):
        return None
    if not isinstance(columns, list):
        print(f"Error: 'columns' debe ser una lista, y se recibió {type(columns).__name__}.")
        return None
    if not isinstance(with_individual_plot, bool):
        print("Error: 'with_individual_plot' debe ser True o False.")
        return None

    significativas = get_features_cat_regression(df, target_col, pvalue)
    if significativas is None:
        return None

    if columns:
        inexistentes = [c for c in columns if c not in df.columns]
        if inexistentes:
            print(f"Error: estas columnas no existen en el DataFrame: {inexistentes}.")
            return None
        significativas = [c for c in significativas if c in columns]

    if not significativas:
        print("Ninguna columna categórica supera el test: no hay nada que pintar.")
        return []

    def _histograma(columna, eje):
        """Dibuja el histograma del target coloreado por categoría."""
        for categoria, grupo in df[[target_col, columna]].dropna().groupby(columna, observed=True):
            eje.hist(grupo[target_col], bins=20, alpha=0.55, label=str(categoria))
        eje.set_title(f"{target_col} según {columna}")
        eje.set_xlabel(target_col)
        eje.set_ylabel("Frecuencia")
        eje.legend(fontsize=8)

    if with_individual_plot:
        # una figura independiente por variable
        for col in significativas:
            fig, ax = plt.subplots(figsize=(8, 4))
            _histograma(col, ax)
            plt.tight_layout()
            plt.show()
    else:
        # todas las variables en una sola figura, en una rejilla de 2 columnas
        n = len(significativas)
        n_cols = min(2, n)
        n_filas = int(np.ceil(n / n_cols))
        fig, axes = plt.subplots(n_filas, n_cols, figsize=(7 * n_cols, 4 * n_filas))
        ejes = np.atleast_1d(axes).ravel()
        for ax, col in zip(ejes, significativas):
            _histograma(col, ax)
        # apaga los subplots sobrantes de la rejilla
        for ax in ejes[n:]:
            ax.axis("off")
        plt.tight_layout()
        plt.show()

    return significativas


# ---------------------------------------------------------------------------
# BONUS: detect_outliers
# ---------------------------------------------------------------------------

def detect_outliers(
    df: pd.DataFrame,
    columns: list = [],
    metodo: str = "iqr",
    umbral: float = 1.5,
) -> Optional[dict]:
    """
    Detecta valores atípicos en las columnas numéricas de un DataFrame.

    Soporta dos métodos:
      - 'iqr': se consideran outliers los valores fuera de
        [Q1 - umbral*IQR, Q3 + umbral*IQR]. Umbral típico: 1.5.
      - 'zscore': se consideran outliers los valores cuyo z-score en valor
        absoluto supera el umbral. Umbral típico: 3.

    Argumentos:
        df (pd.DataFrame): DataFrame a analizar.
        columns (list): columnas a revisar. Si está vacía se usan todas las
            columnas numéricas.
        metodo (str): 'iqr' o 'zscore'.
        umbral (float): factor del IQR o número de desviaciones típicas.

    Retorna:
        dict: un diccionario por columna analizada con las claves 'n_outliers',
        'porcentaje' e 'indices'.
        Retorna None si alguna comprobación de entrada falla.
    """
    if not _es_dataframe(df):
        return None
    if not isinstance(columns, list):
        print(f"Error: 'columns' debe ser una lista, y se recibió {type(columns).__name__}.")
        return None
    if metodo not in ("iqr", "zscore"):
        print(f"Error: 'metodo' debe ser 'iqr' o 'zscore', y se recibió '{metodo}'.")
        return None
    if not _es_float_en_rango(umbral, "umbral", 0, 100):
        return None

    numericas = list(df.select_dtypes(include=np.number).columns)
    if columns:
        inexistentes = [c for c in columns if c not in df.columns]
        if inexistentes:
            print(f"Error: estas columnas no existen en el DataFrame: {inexistentes}.")
            return None
        numericas = [c for c in columns if c in numericas]

    n_filas = len(df)
    resultado = {}

    for col in numericas:
        serie = df[col].dropna()
        if serie.empty:
            resultado[col] = {"n_outliers": 0, "porcentaje": 0.0, "indices": []}
            continue

        if metodo == "iqr":
            q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
            iqr = q3 - q1
            mascara = (serie < q1 - umbral * iqr) | (serie > q3 + umbral * iqr)
        else:
            desviacion = serie.std()
            # si la columna es constante no hay dispersión y no hay outliers
            if desviacion == 0 or pd.isna(desviacion):
                mascara = pd.Series(False, index=serie.index)
            else:
                mascara = ((serie - serie.mean()) / desviacion).abs() > umbral

        indices = serie[mascara].index.tolist()
        resultado[col] = {
            "n_outliers": len(indices),
            "porcentaje": round(len(indices) / n_filas * 100, 2) if n_filas else 0.0,
            "indices": indices,
        }

    return resultado
