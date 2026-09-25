"""
Tests unitarios de toolbox_ml.eda.core.

Para cada función se cubren los tres escenarios que pide el enunciado:
  - caso correcto: input válido -> output esperado
  - caso límite: DataFrame vacío, columna constante, columna con todo nulos...
  - caso de error: input incorrecto -> la función retorna None

Ejecutar con:  pytest tests/ -v
"""

import matplotlib
import numpy as np
import pandas as pd
import pytest

# backend sin ventana: los tests de las funciones de plot no deben abrir figuras
matplotlib.use("Agg")

from toolbox_ml.eda.core import (
    describe_df,
    detect_outliers,
    get_features_cat_regression,
    get_features_num_regression,
    plot_features_cat_regression,
    plot_features_num_regression,
    tipifica_variables,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def df_regresion():
    """DataFrame pequeño y determinista con relaciones conocidas de antemano.

    - 'ruido' es aleatorio pero con semilla fija
    - 'lineal' es exactamente proporcional al target -> correlación 1
    - 'grupo' separa el target en dos bloques que no se solapan
    """
    rng = np.random.default_rng(42)
    n = 60
    target = np.arange(n, dtype=float)
    return pd.DataFrame({
        "target": target,
        "lineal": target * 2 + 1,
        "ruido": rng.normal(size=n),
        "grupo": ["bajo"] * (n // 2) + ["alto"] * (n // 2),
        "constante_cat": ["igual"] * n,
    })


@pytest.fixture
def df_mixto():
    """DataFrame con nulos, tipos variados y cardinalidades distintas."""
    return pd.DataFrame({
        "entero": [1, 2, 3, 4],
        "decimal": [1.5, 2.5, None, 4.5],
        "texto": ["a", "b", "c", "d"],
        "binaria": [True, False, True, False],
    })


# ===========================================================================
# describe_df
# ===========================================================================

def test_describe_df_devuelve_dataframe(df_mixto):
    """Caso correcto: input válido -> retorna un DataFrame."""
    resultado = describe_df(df_mixto)
    assert isinstance(resultado, pd.DataFrame)


def test_describe_df_columnas_y_filas_correctas(df_mixto):
    """El resultado tiene las 4 columnas esperadas y una fila por columna del input."""
    resultado = describe_df(df_mixto)
    assert set(resultado.columns) == {
        "tipo", "porcentaje_nulos", "valores_unicos", "porcentaje_cardinalidad"
    }
    assert list(resultado.index) == list(df_mixto.columns)


def test_describe_df_calcula_bien_nulos_y_cardinalidad():
    """Los porcentajes de nulos y de cardinalidad se calculan correctamente."""
    df = pd.DataFrame({"a": [1, None, None, None], "b": [1, 2, 3, 4]})
    resultado = describe_df(df)
    assert resultado.loc["a", "porcentaje_nulos"] == pytest.approx(75.0)
    assert resultado.loc["b", "porcentaje_nulos"] == pytest.approx(0.0)
    assert resultado.loc["b", "valores_unicos"] == 4
    assert resultado.loc["b", "porcentaje_cardinalidad"] == pytest.approx(100.0)


def test_describe_df_dataframe_sin_filas():
    """Caso límite: un DataFrame con columnas pero sin filas no debe romper."""
    df = pd.DataFrame({"a": [], "b": []})
    resultado = describe_df(df)
    assert isinstance(resultado, pd.DataFrame)
    assert resultado.loc["a", "porcentaje_nulos"] == 0.0


def test_describe_df_retorna_none_con_input_invalido():
    """Caso de error: lo que no sea un DataFrame -> None."""
    assert describe_df("esto no es un dataframe") is None
    assert describe_df([1, 2, 3]) is None
    assert describe_df(None) is None


# ===========================================================================
# tipifica_variables
# ===========================================================================

def test_tipifica_variables_estructura(df_mixto):
    """Caso correcto: devuelve las dos columnas pedidas, una fila por variable."""
    resultado = tipifica_variables(df_mixto, umbral_categoria=3, umbral_continua=50.0)
    assert isinstance(resultado, pd.DataFrame)
    assert list(resultado.columns) == ["nombre_variable", "tipo_sugerido"]
    assert len(resultado) == df_mixto.shape[1]


def test_tipifica_variables_aplica_bien_la_cascada():
    """Cada rama de la cascada devuelve el tipo que corresponde."""
    df = pd.DataFrame({
        "bin": [0, 1] * 10,                 # cardinalidad 2 -> Binaria
        "cat": ["a", "b", "c"] * 6 + ["a", "b"],  # cardinalidad 3 < 5 -> Categórica
        "continua": np.arange(20.0),        # card 20, %card 100 >= 50 -> Continua
        "discreta": [i % 6 for i in range(20)],  # card 6 >= 5, %card 30 < 50 -> Discreta
    })
    res = tipifica_variables(df, umbral_categoria=5, umbral_continua=50.0)
    tipos = dict(zip(res["nombre_variable"], res["tipo_sugerido"]))
    assert tipos["bin"] == "Binaria"
    assert tipos["cat"] == "Categórica"
    assert tipos["continua"] == "Numérica Continua"
    assert tipos["discreta"] == "Numérica Discreta"


def test_tipifica_variables_dataframe_sin_filas():
    """Caso límite: sin filas la función sigue devolviendo una fila por columna."""
    resultado = tipifica_variables(pd.DataFrame({"a": [], "b": []}), 5, 50.0)
    assert len(resultado) == 2


def test_tipifica_variables_retorna_none_con_umbrales_invalidos(df_mixto):
    """Caso de error: umbrales fuera de rango o de tipo incorrecto -> None."""
    assert tipifica_variables(df_mixto, umbral_categoria=-1, umbral_continua=50.0) is None
    assert tipifica_variables(df_mixto, umbral_categoria="cinco", umbral_continua=50.0) is None
    assert tipifica_variables(df_mixto, umbral_categoria=5, umbral_continua=150.0) is None
    assert tipifica_variables("no soy un df", 5, 50.0) is None


# ===========================================================================
# get_features_num_regression
# ===========================================================================

def test_get_features_num_regression_detecta_la_correlacionada(df_regresion):
    """Caso correcto: la variable proporcional al target entra; el ruido no."""
    resultado = get_features_num_regression(df_regresion, "target", umbral_corr=0.8)
    assert resultado == ["lineal"]


def test_get_features_num_regression_excluye_el_propio_target(df_regresion):
    """El target nunca debe aparecer en la lista de features seleccionadas."""
    resultado = get_features_num_regression(df_regresion, "target", umbral_corr=0.0)
    assert "target" not in resultado


def test_get_features_num_regression_filtra_por_pvalue(df_regresion):
    """Con un pvalue muy exigente, el ruido no significativo queda fuera."""
    con_filtro = get_features_num_regression(
        df_regresion, "target", umbral_corr=0.0, pvalue=0.001
    )
    assert "ruido" not in con_filtro
    assert "lineal" in con_filtro


def test_get_features_num_regression_columna_constante():
    """Caso límite: una columna constante no tiene correlación definida y se ignora."""
    df = pd.DataFrame({"target": [1.0, 2, 3, 4, 5], "cte": [7, 7, 7, 7, 7]})
    assert get_features_num_regression(df, "target", umbral_corr=0.0) == []


def test_get_features_num_regression_retorna_none_con_errores(df_regresion):
    """Caso de error: target inexistente, target no numérico o umbral fuera de rango."""
    assert get_features_num_regression(df_regresion, "no_existe", 0.5) is None
    assert get_features_num_regression(df_regresion, "grupo", 0.5) is None
    assert get_features_num_regression(df_regresion, "target", umbral_corr=5) is None
    assert get_features_num_regression(df_regresion, "target", 0.5, pvalue=2) is None
    assert get_features_num_regression("no soy un df", "target", 0.5) is None


# ===========================================================================
# plot_features_num_regression
# ===========================================================================

def test_plot_features_num_regression_devuelve_las_pintadas(df_regresion):
    """Caso correcto: devuelve la lista de columnas representadas."""
    resultado = plot_features_num_regression(df_regresion, "target", umbral_corr=0.8)
    assert resultado == ["lineal"]


def test_plot_features_num_regression_respeta_columns(df_regresion):
    """Si se pasa 'columns', el resultado es la intersección con las significativas."""
    resultado = plot_features_num_regression(
        df_regresion, "target", columns=["ruido"], umbral_corr=0.8
    )
    assert resultado == []


def test_plot_features_num_regression_divide_en_grupos_de_cinco():
    """Caso límite: con más de 5 columnas se pintan varios pairplots sin fallar."""
    rng = np.random.default_rng(0)
    n = 40
    target = np.arange(n, dtype=float)
    datos = {"target": target}
    for i in range(7):
        datos[f"f{i}"] = target * (i + 1) + rng.normal(scale=0.5, size=n)
    resultado = plot_features_num_regression(pd.DataFrame(datos), "target", umbral_corr=0.5)
    assert len(resultado) == 7


def test_plot_features_num_regression_retorna_none_con_errores(df_regresion):
    """Caso de error: argumentos inválidos -> None."""
    assert plot_features_num_regression(df_regresion, "no_existe") is None
    assert plot_features_num_regression(df_regresion, "target", columns="no soy lista") is None
    assert plot_features_num_regression(df_regresion, "target", umbral_corr=-1) is None


# ===========================================================================
# get_features_cat_regression
# ===========================================================================

def test_get_features_cat_regression_detecta_la_significativa(df_regresion):
    """Caso correcto: 'grupo' separa el target en dos bloques -> significativa."""
    resultado = get_features_cat_regression(df_regresion, "target", pvalue=0.05)
    assert "grupo" in resultado


def test_get_features_cat_regression_ignora_categoricas_constantes(df_regresion):
    """Una categórica con un solo valor no puede compararse: queda fuera."""
    resultado = get_features_cat_regression(df_regresion, "target", pvalue=0.05)
    assert "constante_cat" not in resultado


def test_get_features_cat_regression_usa_anova_con_mas_de_dos_grupos():
    """Caso límite: con 3 categorías se usa ANOVA y se detecta la diferencia."""
    df = pd.DataFrame({
        "target": [1.0, 1.1, 1.2, 5.0, 5.1, 5.2, 9.0, 9.1, 9.2],
        "tres": ["a", "a", "a", "b", "b", "b", "c", "c", "c"],
    })
    assert get_features_cat_regression(df, "target", pvalue=0.05) == ["tres"]


def test_get_features_cat_regression_retorna_none_con_errores(df_regresion):
    """Caso de error: target inválido o pvalue fuera de rango -> None."""
    assert get_features_cat_regression(df_regresion, "no_existe") is None
    assert get_features_cat_regression(df_regresion, "grupo") is None
    assert get_features_cat_regression(df_regresion, "target", pvalue=1.5) is None
    assert get_features_cat_regression([1, 2, 3], "target") is None


# ===========================================================================
# plot_features_cat_regression
# ===========================================================================

def test_plot_features_cat_regression_devuelve_las_pintadas(df_regresion):
    """Caso correcto: devuelve las categóricas que superaron el test."""
    resultado = plot_features_cat_regression(df_regresion, "target")
    assert "grupo" in resultado


def test_plot_features_cat_regression_modo_individual(df_regresion):
    """with_individual_plot=True devuelve el mismo resultado que el modo agrupado."""
    agrupado = plot_features_cat_regression(df_regresion, "target", with_individual_plot=False)
    individual = plot_features_cat_regression(df_regresion, "target", with_individual_plot=True)
    assert agrupado == individual


def test_plot_features_cat_regression_sin_significativas():
    """Caso límite: si ninguna supera el test, devuelve lista vacía (no None)."""
    df = pd.DataFrame({"target": [1.0, 2, 3, 4], "cat": ["a", "a", "a", "a"]})
    assert plot_features_cat_regression(df, "target") == []


def test_plot_features_cat_regression_retorna_none_con_errores(df_regresion):
    """Caso de error: argumentos inválidos -> None."""
    assert plot_features_cat_regression(df_regresion, "no_existe") is None
    assert plot_features_cat_regression(df_regresion, "target", columns="no lista") is None
    assert plot_features_cat_regression(df_regresion, "target", with_individual_plot="si") is None


# ===========================================================================
# detect_outliers (bonus)
# ===========================================================================

def test_detect_outliers_encuentra_el_valor_extremo():
    """Caso correcto: el 1000 en una serie de dígitos es un outlier por IQR."""
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5, 6, 7, 8, 9, 1000]})
    resultado = detect_outliers(df, metodo="iqr")
    assert resultado["a"]["n_outliers"] == 1
    assert resultado["a"]["indices"] == [9]
    assert resultado["a"]["porcentaje"] == pytest.approx(10.0)


def test_detect_outliers_metodo_zscore():
    """El método z-score también localiza el extremo y devuelve la misma estructura."""
    df = pd.DataFrame({"a": [10.0] * 30 + [500.0]})
    resultado = detect_outliers(df, metodo="zscore", umbral=3)
    assert set(resultado["a"].keys()) == {"n_outliers", "porcentaje", "indices"}
    assert resultado["a"]["n_outliers"] >= 0


def test_detect_outliers_columna_constante_y_vacia():
    """Caso límite: columnas constantes o todo-nulos no producen outliers."""
    df = pd.DataFrame({"cte": [5.0] * 10, "nulos": [np.nan] * 10})
    resultado = detect_outliers(df, metodo="zscore", umbral=3)
    assert resultado["cte"]["n_outliers"] == 0
    assert resultado["nulos"]["n_outliers"] == 0


def test_detect_outliers_retorna_none_con_errores():
    """Caso de error: método desconocido, columnas inexistentes o input inválido."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    assert detect_outliers(df, metodo="inventado") is None
    assert detect_outliers(df, columns=["no_existe"]) is None
    assert detect_outliers("no soy un df") is None
