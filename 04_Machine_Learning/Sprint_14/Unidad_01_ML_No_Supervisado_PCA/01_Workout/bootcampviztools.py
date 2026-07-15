"""
Visualización para variables categóricas y numéricas.
"""

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# ---------------------------------------------------------------------------
# Función privada de utilidad — no forma parte de la API pública del módulo
# ---------------------------------------------------------------------------

def _split_in_chunks(items: list, chunk_size: int) -> list[list]:
    """
    Divide una lista en sublistas de tamaño máximo chunk_size.

    Argumentos:
        items (list): Lista de elementos a dividir.
        chunk_size (int): Número máximo de elementos por sublista.

    Retorna:
        list[list]: Lista de sublistas.
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


# ---------------------------------------------------------------------------
# Distribución de variables categóricas
# ---------------------------------------------------------------------------

def pinta_distribucion_categoricas(
    df: pd.DataFrame,
    columnas_categoricas: list,
    relativa: bool = False,
    mostrar_valores: bool = False,
    y_padding: float = 0.15,
) -> None:
    """
    Pinta un gráfico de barras por cada columna categórica indicada.

    Argumentos:
        df (pd.DataFrame): DataFrame que contiene los datos.
        columnas_categoricas (list): Lista de nombres de columnas categóricas a representar.
        relativa (bool): Si es True, usa frecuencias relativas en lugar de absolutas.
            Por defecto False.
        mostrar_valores (bool): Si es True, anota el valor numérico encima de cada barra.
            Por defecto False.
        y_padding (float): Fracción de margen adicional sobre el valor máximo del eje Y.
            Evita que las anotaciones queden cortadas. Por defecto 0.15 (15%).
    """
    if not columnas_categoricas:
        return

    n_cols = len(columnas_categoricas)
    n_rows = math.ceil(n_cols / 2)

    fig, axes = plt.subplots(n_rows, 2, figsize=(15, 5 * n_rows))
    axes = axes.flatten()

    for i, col in enumerate(columnas_categoricas):
        ax = axes[i]
        counts = df[col].value_counts()
        serie = counts / counts.sum() if relativa else counts

        sns.barplot(x=serie.index, y=serie, ax=ax, palette="viridis",
                    hue=serie.index, legend=False)

        ax.set_title(f"Distribución de {col}")
        ax.set_xlabel("")
        ax.set_ylabel("Frecuencia Relativa" if relativa else "Frecuencia")
        ax.tick_params(axis="x", rotation=45)

        # Ampliar el eje Y para que las anotaciones no queden cortadas
        current_max = serie.max()
        ax.set_ylim(0, current_max * (1 + y_padding))

        if mostrar_valores:
            for p in ax.patches:
                ax.annotate(
                    f"{p.get_height():.2f}",
                    (p.get_x() + p.get_width() / 2.0, p.get_height()),
                    ha="center", va="bottom", xytext=(0, 5),
                    textcoords="offset points",
                )

    # Ocultar los ejes sobrantes si el número de columnas es impar
    for j in range(i + 1, n_rows * 2):
        axes[j].axis("off")

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Relación entre dos variables categóricas
# ---------------------------------------------------------------------------

def plot_categorical_relationship(
    df: pd.DataFrame,
    cat_col1: str,
    cat_col2: str,
    relative_freq: bool = False,
    show_values: bool = False,
    size_group: int = 5,
    y_padding: float = 0.15,
) -> None:
    """
    Pinta un gráfico de barras agrupado que muestra la relación entre dos variables
    categóricas. Si cat_col1 tiene más de size_group categorías únicas, divide los
    gráficos en grupos para mejorar la legibilidad. Todos los grupos comparten
    el mismo eje Y para que sean comparables entre sí.

    Argumentos:
        df (pd.DataFrame): DataFrame que contiene los datos.
        cat_col1 (str): Columna categórica para el eje X.
        cat_col2 (str): Columna categórica para el color (hue).
        relative_freq (bool): Si es True, convierte los conteos a frecuencias relativas
            dentro de cada categoría de cat_col1. Por defecto False.
        show_values (bool): Si es True, anota el valor encima de cada barra.
            Por defecto False.
        size_group (int): Número máximo de categorías de cat_col1 por gráfico.
            Por defecto 5.
        y_padding (float): Fracción de margen adicional sobre el valor máximo global
            del eje Y. Garantiza escala uniforme entre grupos y evita que las
            anotaciones queden cortadas. Por defecto 0.15 (15%).
    """
    count_data = df.groupby([cat_col1, cat_col2]).size().reset_index(name="count")

    if relative_freq:
        totals = df[cat_col1].value_counts()
        count_data["count"] = count_data.apply(
            lambda row: row["count"] / totals[row[cat_col1]], axis=1
        )

    # Máximo global calculado una sola vez para que todos los chunks
    # compartan el mismo eje Y independientemente de sus valores locales
    global_max = count_data["count"].max()
    y_limit = (0, global_max * (1 + y_padding))

    unique_categories = df[cat_col1].unique().tolist()
    chunks = _split_in_chunks(unique_categories, size_group)

    for idx, chunk in enumerate(chunks):
        subset = count_data[count_data[cat_col1].isin(chunk)]

        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=cat_col1, y="count", hue=cat_col2, data=subset, order=chunk)
        ax.set_ylim(y_limit)

        title_suffix = f" — Grupo {idx + 1} de {len(chunks)}" if len(chunks) > 1 else ""
        plt.title(f"Relación entre {cat_col1} y {cat_col2}{title_suffix}")
        plt.xlabel(cat_col1)
        plt.ylabel("Frecuencia Relativa" if relative_freq else "Conteo")
        plt.xticks(rotation=45)

        if show_values:
            for p in ax.patches:
                ax.annotate(
                    f"{p.get_height():.2f}",
                    (p.get_x() + p.get_width() / 2.0, p.get_height()),
                    ha="center", va="center", fontsize=10, color="black",
                    xytext=(0, size_group), textcoords="offset points",
                )

        plt.tight_layout()
        plt.show()


# ---------------------------------------------------------------------------
# Relación entre variable categórica y variable numérica (media o mediana)
# ---------------------------------------------------------------------------

def plot_categorical_numerical_relationship(
    df: pd.DataFrame,
    categorical_col: str,
    numerical_col: str,
    show_values: bool = False,
    measure: str = "mean",
    size_group: int = 5,
    y_padding: float = 0.15,
) -> None:
    """
    Pinta un gráfico de barras con la media o mediana de una variable numérica
    agrupada por una variable categórica. Si la categórica tiene más de size_group
    categorías, divide la visualización en grupos. Todos los grupos comparten
    el mismo eje Y para que sean comparables entre sí.

    Argumentos:
        df (pd.DataFrame): DataFrame que contiene los datos.
        categorical_col (str): Nombre de la columna categórica (eje X).
        numerical_col (str): Nombre de la columna numérica (eje Y).
        show_values (bool): Si es True, anota el valor encima de cada barra.
            Por defecto False.
        measure (str): Medida de tendencia central a representar: 'mean' o 'median'.
            Por defecto 'mean'.
        size_group (int): Número máximo de categorías por gráfico. Por defecto 5.
        y_padding (float): Fracción de margen adicional sobre el valor máximo global
            del eje Y. Garantiza escala uniforme entre grupos y evita que las
            anotaciones queden cortadas. Por defecto 0.15 (15%).
    """
    if measure not in ("mean", "median"):
        print(f"measure='{measure}' no es válido. Usa 'mean' o 'median'. Se usará 'mean'.")
        measure = "mean"

    if measure == "median":
        grouped = df.groupby(categorical_col)[numerical_col].median()
    else:
        grouped = df.groupby(categorical_col)[numerical_col].mean()

    grouped = grouped.sort_values(ascending=False)

    # Máximo global calculado una sola vez — todos los chunks usarán este límite
    global_max = grouped.max()
    y_limit = (0, global_max * (1 + y_padding))

    chunks = _split_in_chunks(grouped.index.tolist(), size_group)

    for idx, chunk in enumerate(chunks):
        subset = grouped.loc[chunk]

        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=subset.index, y=subset.values)
        ax.set_ylim(y_limit)

        title_suffix = f" — Grupo {idx + 1} de {len(chunks)}" if len(chunks) > 1 else ""
        plt.title(f"Relación entre {categorical_col} y {numerical_col}{title_suffix}")
        plt.xlabel(categorical_col)
        plt.ylabel(f"{measure.capitalize()} de {numerical_col}")
        plt.xticks(rotation=45)

        if show_values:
            for p in ax.patches:
                ax.annotate(
                    f"{p.get_height():.2f}",
                    (p.get_x() + p.get_width() / 2.0, p.get_height()),
                    ha="center", va="center", fontsize=10, color="black",
                    xytext=(0, 5), textcoords="offset points",
                )

        plt.tight_layout()
        plt.show()


# ---------------------------------------------------------------------------
# Histograma + KDE y boxplot combinados para variables numéricas
# ---------------------------------------------------------------------------

def plot_combined_graphs(
    df: pd.DataFrame,
    columns: list,
    whisker_width: float = 1.5,
    bins: int | None = None,
) -> None:
    """
    Para cada columna numérica indicada, pinta un histograma con KDE y un boxplot
    uno al lado del otro.

    Argumentos:
        df (pd.DataFrame): DataFrame que contiene los datos.
        columns (list): Lista de columnas numéricas a representar.
        whisker_width (float): Multiplicador del IQR para los bigotes del boxplot.
            Por defecto 1.5.
        bins (int | None): Número de bins del histograma. Si es None, se calcula
            automáticamente. Por defecto None.
    """
    num_cols = len(columns)
    if not num_cols:
        return

    fig, axes = plt.subplots(num_cols, 2, figsize=(12, 5 * num_cols))
    # Garantiza que axes sea siempre 2D aunque haya una sola columna
    if num_cols == 1:
        axes = axes[np.newaxis, :]

    for i, column in enumerate(columns):
        if not pd.api.types.is_numeric_dtype(df[column]):
            continue

        sns.histplot(df[column], kde=True, ax=axes[i, 0],
                     bins="auto" if bins is None else bins)
        axes[i, 0].set_title(f"Histograma y KDE de {column}")

        sns.boxplot(x=df[column], ax=axes[i, 1], whis=whisker_width)
        axes[i, 1].set_title(f"Boxplot de {column}")

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Boxplots agrupados por categoría
# ---------------------------------------------------------------------------

def plot_grouped_boxplots(
    df: pd.DataFrame,
    cat_col: str,
    num_col: str,
    size_group: int = 5,
    y_padding: float = 0.05,
) -> None:
    """
    Pinta boxplots de una variable numérica agrupados por una variable categórica.
    Si la categórica tiene más de size_group categorías, divide la visualización
    en grupos. Todos los grupos comparten el mismo eje Y para que sean comparables.

    Argumentos:
        df (pd.DataFrame): DataFrame que contiene los datos.
        cat_col (str): Nombre de la columna categórica (eje X).
        num_col (str): Nombre de la columna numérica (eje Y).
        size_group (int): Número máximo de categorías por gráfico. Por defecto 5.
        y_padding (float): Fracción de margen adicional sobre el rango global
            del eje Y. Por defecto 0.05 (5%).
    """
    # Rango global calculado sobre todos los datos — no sobre cada chunk
    global_min = df[num_col].min()
    global_max = df[num_col].max()
    value_range = global_max - global_min
    y_limit = (
        global_min - value_range * y_padding,
        global_max + value_range * y_padding,
    )

    unique_cats = df[cat_col].unique().tolist()
    chunks = _split_in_chunks(unique_cats, size_group)

    for idx, chunk in enumerate(chunks):
        subset = df[df[cat_col].isin(chunk)]

        plt.figure(figsize=(10, 6))
        ax = sns.boxplot(x=cat_col, y=num_col, data=subset, order=chunk)
        ax.set_ylim(y_limit)

        title_suffix = f" (Grupo {idx + 1} de {len(chunks)})" if len(chunks) > 1 else ""
        plt.title(f"Boxplots of {num_col} for {cat_col}{title_suffix}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


# ---------------------------------------------------------------------------
# Histogramas agrupados por categoría
# ---------------------------------------------------------------------------

def plot_grouped_histograms(
    df: pd.DataFrame,
    cat_col: str,
    num_col: str,
    group_size: int = 5,
    y_padding: float = 0.15,
) -> None:
    """
    Pinta histogramas solapados de una variable numérica, uno por cada categoría
    de cat_col. Si la categórica tiene más de group_size categorías, divide la
    visualización en grupos. Todos los grupos comparten el mismo eje Y para que
    sean comparables.

    Argumentos:
        df (pd.DataFrame): DataFrame que contiene los datos.
        cat_col (str): Nombre de la columna categórica usada para agrupar.
        num_col (str): Nombre de la columna numérica representada en el eje X.
        group_size (int): Número máximo de categorías por gráfico. Por defecto 5.
        y_padding (float): Fracción de margen adicional sobre el conteo máximo global.
            Por defecto 0.15 (15%).
    """
    # Calcular el conteo máximo global usando numpy para no depender del
    # cálculo interno de seaborn, que varía por chunk
    counts, _ = np.histogram(df[num_col].dropna(), bins="auto")
    global_y_max = counts.max() * (1 + y_padding)

    unique_cats = df[cat_col].unique().tolist()
    chunks = _split_in_chunks(unique_cats, group_size)

    for idx, chunk in enumerate(chunks):
        subset = df[df[cat_col].isin(chunk)]

        fig, ax = plt.subplots(figsize=(10, 6))
        for cat in chunk:
            sns.histplot(
                subset[subset[cat_col] == cat][num_col],
                kde=True, label=str(cat), ax=ax,
            )

        ax.set_ylim(0, global_y_max)

        title_suffix = f" (Grupo {idx + 1} de {len(chunks)})" if len(chunks) > 1 else ""
        plt.title(f"Histograms of {num_col} for {cat_col}{title_suffix}")
        plt.xlabel(num_col)
        plt.ylabel("Frequency")
        plt.legend()
        plt.tight_layout()
        plt.show()


# ---------------------------------------------------------------------------
# Diagrama de dispersión con correlación opcional
# ---------------------------------------------------------------------------

def grafico_dispersion_con_correlacion(
    df: pd.DataFrame,
    columna_x: str,
    columna_y: str,
    tamano_puntos: int = 50,
    mostrar_correlacion: bool = False,
) -> None:
    """
    Crea un diagrama de dispersión entre dos columnas y opcionalmente muestra
    la correlación de Pearson en el título.

    Argumentos:
        df (pd.DataFrame): DataFrame que contiene los datos.
        columna_x (str): Nombre de la columna para el eje X.
        columna_y (str): Nombre de la columna para el eje Y.
        tamano_puntos (int): Tamaño de los puntos en el gráfico. Por defecto 50.
        mostrar_correlacion (bool): Si es True, muestra la correlación en el título.
            Por defecto False.
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x=columna_x, y=columna_y, s=tamano_puntos)

    if mostrar_correlacion:
        correlacion = df[columna_x].corr(df[columna_y])
        plt.title(f"Diagrama de Dispersión con Correlación: {correlacion:.2f}")
    else:
        plt.title("Diagrama de Dispersión")

    plt.xlabel(columna_x)
    plt.ylabel(columna_y)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Bubble chart
# ---------------------------------------------------------------------------

def bubble_plot(
    df: pd.DataFrame,
    col_x: str,
    col_y: str,
    col_size: str,
    scale: float = 1000.0,
) -> None:
    """
    Crea un scatter plot usando dos columnas para los ejes X e Y y una tercera
    columna para determinar el tamaño de los puntos.

    Argumentos:
        df (pd.DataFrame): DataFrame que contiene los datos.
        col_x (str): Nombre de la columna para el eje X.
        col_y (str): Nombre de la columna para el eje Y.
        col_size (str): Nombre de la columna para determinar el tamaño de los puntos.
        scale (float): Divisor aplicado a los tamaños normalizados para controlar
            el radio visual de las burbujas. Por defecto 1000.
    """
    # Normalización min-max desplazada para garantizar tamaños positivos
    sizes = (df[col_size] - df[col_size].min() + 1) / scale

    plt.figure(figsize=(10, 6))
    plt.scatter(df[col_x], df[col_y], s=sizes)
    plt.xlabel(col_x)
    plt.ylabel(col_y)
    plt.title(f"Burbujas de {col_x} vs {col_y} con Tamaño basado en {col_size}")
    plt.tight_layout()
    plt.show()