# -*- coding: utf-8 -*-
"""
Funciones y diccionarios de apoyo para el proyecto de prediccion de cesareas.
Los codigos de provincia son los oficiales del INE (2 digitos).
"""

import pandas as pd

# ---------------------------------------------------------------
# Mapa provincia (codigo INE) -> Comunidad Autonoma
# ---------------------------------------------------------------
CCAA_PROVINCIAS = {
    "Andalucía": ["04", "11", "14", "18", "21", "23", "29", "41"],
    "Aragón": ["22", "44", "50"],
    "Asturias": ["33"],
    "Baleares": ["07"],
    "Canarias": ["35", "38"],
    "Cantabria": ["39"],
    "Castilla y León": ["05", "09", "24", "34", "37", "40", "42", "47", "49"],
    "Castilla-La Mancha": ["02", "13", "16", "19", "45"],
    "Cataluña": ["08", "17", "25", "43"],
    "C. Valenciana": ["03", "12", "46"],
    "Extremadura": ["06", "10"],
    "Galicia": ["15", "27", "32", "36"],
    "Madrid": ["28"],
    "Murcia": ["30"],
    "Navarra": ["31"],
    "País Vasco": ["01", "20", "48"],
    "La Rioja": ["26"],
    "Ceuta": ["51"],
    "Melilla": ["52"],
}

# Le damos la vuelta para poder hacer un .map() directo: codigo -> CCAA
PROV_A_CCAA = {prov: ccaa for ccaa, provs in CCAA_PROVINCIAS.items() for prov in provs}


def calidad_datos(df):
    """Resumen rapido de calidad de un DataFrame: tipo, nulos, % nulos y valores unicos.
    (Sacada de la guia orientativa del EDA, paso 06)."""
    resumen = pd.DataFrame({
        "dtype": df.dtypes,
        "nulos": df.isnull().sum(),
        "pct_nulos": (df.isnull().sum() / len(df) * 100).round(2),
        "unicos": df.nunique(),
    })
    return resumen


def tasa_por_grupo(df, col_grupo, col_binaria, valor_positivo=1):
    """Devuelve la tasa (%) de valor_positivo de col_binaria por cada grupo de col_grupo,
    ordenada de mayor a menor. La uso constantemente en el analisis bivariante."""
    tasa = (df.groupby(col_grupo, observed=True)[col_binaria]
              .apply(lambda s: (s == valor_positivo).mean() * 100)
              .sort_values(ascending=False)
              .round(1))
    return tasa
