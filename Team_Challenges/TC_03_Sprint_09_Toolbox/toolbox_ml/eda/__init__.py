"""Subpaquete de análisis exploratorio de datos."""

from toolbox_ml.eda.core import (
    describe_df,
    detect_outliers,
    get_features_cat_regression,
    get_features_num_regression,
    plot_features_cat_regression,
    plot_features_num_regression,
    tipifica_variables,
)

__all__ = [
    "describe_df",
    "tipifica_variables",
    "get_features_num_regression",
    "plot_features_num_regression",
    "get_features_cat_regression",
    "plot_features_cat_regression",
    "detect_outliers",
]
