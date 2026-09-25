"""
Genera docs/er_diagram.png a partir de la definición de src/esquema.py.

Se dibuja con matplotlib en lugar de exportarlo de dbdiagram.io para que el
diagrama no pueda quedar desfasado respecto al modelo: si alguien añade un campo
en esquema.py, basta con volver a ejecutar este script y el PNG se actualiza.

Uso:
    python docs/generar_diagrama.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.esquema import ESQUEMA, foraneas  # noqa: E402

# --- Paleta -----------------------------------------------------------------
TINTA = "#1b2430"
SUAVE = "#5b6b7f"
LINEA = "#c3ccd8"
CABECERA = "#2f5d8c"
CABECERA_TXT = "#ffffff"
PK_COLOR = "#b8562c"
FK_COLOR = "#2f7d5f"
FONDO = "#ffffff"

# --- Posición de cada tabla en la rejilla (x, y del borde superior izquierdo) -
POSICIONES = {
    "categories":  (0.5, 9.2),
    "products":    (0.5, 6.4),
    "customers":   (5.2, 9.2),
    "orders":      (5.2, 6.0),
    "order_items": (5.2, 2.2),
    "payments":    (10.0, 6.0),
    "reviews":     (10.0, 2.2),
}

ANCHO = 4.0
ALTO_CABECERA = 0.42
ALTO_FILA = 0.30


def dibujar_tabla(ax, nombre, x, y):
    """Dibuja una caja de tabla y devuelve la posición vertical de cada campo."""
    campos = ESQUEMA[nombre]
    alto = ALTO_CABECERA + ALTO_FILA * len(campos)

    # cuerpo
    ax.add_patch(FancyBboxPatch(
        (x, y - alto), ANCHO, alto,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.1, edgecolor=LINEA, facecolor=FONDO, zorder=2,
    ))
    # cabecera
    ax.add_patch(FancyBboxPatch(
        (x, y - ALTO_CABECERA), ANCHO, ALTO_CABECERA,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=0, facecolor=CABECERA, zorder=3,
    ))
    ax.text(x + ANCHO / 2, y - ALTO_CABECERA / 2, nombre,
            ha="center", va="center", fontsize=10.5, fontweight="bold",
            color=CABECERA_TXT, family="monospace", zorder=4)

    posiciones_campo = {}
    for i, (campo, tipo, modo, clave, _) in enumerate(campos):
        cy = y - ALTO_CABECERA - ALTO_FILA * (i + 0.5)
        posiciones_campo[campo] = cy

        if clave == "PK":
            marca, color, peso = "PK", PK_COLOR, "bold"
        elif clave.startswith("FK"):
            marca, color, peso = "FK", FK_COLOR, "bold"
        else:
            marca, color, peso = "  ", SUAVE, "normal"

        ax.text(x + 0.10, cy, marca, ha="left", va="center", fontsize=6.4,
                color=color, fontweight="bold", family="monospace", zorder=4)
        ax.text(x + 0.42, cy, campo, ha="left", va="center", fontsize=7.6,
                color=TINTA, fontweight=peso, family="monospace", zorder=4)
        etiqueta_tipo = tipo if modo == "REQUIRED" else f"{tipo}?"
        ax.text(x + ANCHO - 0.10, cy, etiqueta_tipo, ha="right", va="center",
                fontsize=6.4, color=SUAVE, family="monospace", zorder=4)

        ax.plot([x + 0.06, x + ANCHO - 0.06], [cy - ALTO_FILA / 2] * 2,
                color=LINEA, linewidth=0.4, zorder=3)

    return posiciones_campo, alto


def main():
    fig, ax = plt.subplots(figsize=(15.5, 10.5))
    ax.set_xlim(0, 14.5)
    ax.set_ylim(0, 10.6)
    ax.axis("off")
    fig.patch.set_facecolor(FONDO)

    campos_por_tabla = {}
    for nombre, (x, y) in POSICIONES.items():
        campos_por_tabla[nombre], _ = dibujar_tabla(ax, nombre, x, y)

    # --- Relaciones: de la FK (lado N) a la PK (lado 1) ---------------------
    for tabla in ESQUEMA:
        for campo, tabla_destino, campo_destino in foraneas(tabla):
            x_o = POSICIONES[tabla][0]
            y_o = campos_por_tabla[tabla][campo]
            x_d = POSICIONES[tabla_destino][0]
            y_d = campos_por_tabla[tabla_destino][campo_destino]

            # sale y entra por el lado que quede más corto
            origen = (x_o + ANCHO, y_o) if x_d >= x_o else (x_o, y_o)
            destino = (x_d, y_d) if x_d >= x_o else (x_d + ANCHO, y_d)

            ax.add_patch(FancyArrowPatch(
                origen, destino,
                connectionstyle="arc3,rad=0.16",
                arrowstyle="-|>", mutation_scale=11,
                linewidth=1.1, color=FK_COLOR, alpha=0.75, zorder=1,
            ))
            # cardinalidad: N en el origen (la tabla con la FK), 1 en el destino
            ax.text(origen[0] + (0.12 if x_d >= x_o else -0.12), origen[1] + 0.10,
                    "N", fontsize=7.5, color=FK_COLOR, fontweight="bold",
                    ha="left" if x_d >= x_o else "right", zorder=5)
            ax.text(destino[0] - (0.12 if x_d >= x_o else -0.12), destino[1] + 0.10,
                    "1", fontsize=7.5, color=FK_COLOR, fontweight="bold",
                    ha="right" if x_d >= x_o else "left", zorder=5)

    # --- Títulos y leyenda --------------------------------------------------
    ax.text(0.5, 10.35, "VoltiaTech — Modelo entidad-relación",
            fontsize=17, fontweight="bold", color=TINTA, ha="left")
    ax.text(0.5, 10.05,
            "E-commerce de electrónica · 7 tablas normalizadas hasta 3NF · Google BigQuery",
            fontsize=9.5, color=SUAVE, ha="left")

    leyenda = [
        (PK_COLOR, "PK", "clave primaria"),
        (FK_COLOR, "FK", "clave foránea"),
        (SUAVE, "?", "campo NULLABLE"),
    ]
    # la leyenda y las notas van en el hueco libre de abajo a la izquierda,
    # para no solaparse con ninguna tabla
    ax.text(0.5, 3.55, "LEYENDA", fontsize=8, color=TINTA, fontweight="bold",
            family="monospace", ha="left")
    for i, (color, marca, texto) in enumerate(leyenda):
        y = 3.22 - i * 0.28
        ax.text(0.5, y, marca, fontsize=8, color=color, fontweight="bold",
                family="monospace", ha="left")
        ax.text(1.0, y, texto, fontsize=8, color=SUAVE, ha="left")
    ax.text(0.5, 2.36, "N -> 1", fontsize=8, color=FK_COLOR, fontweight="bold",
            family="monospace", ha="left")
    ax.text(1.4, 2.36, "la flecha va de la FK a la PK que referencia",
            fontsize=8, color=SUAVE, ha="left")

    ax.plot([0.5, 4.3], [2.02, 2.02], color=LINEA, linewidth=0.8)
    ax.text(0.5, 1.70,
            "La relación N:M entre orders y products se resuelve con la tabla",
            fontsize=8.5, color=SUAVE, ha="left")
    ax.text(0.5, 1.44,
            "intermedia order_items, que guarda unit_price: el precio pactado",
            fontsize=8.5, color=SUAVE, ha="left")
    ax.text(0.5, 1.18,
            "en la compra, no el precio actual del catálogo.",
            fontsize=8.5, color=SUAVE, ha="left")

    salida = os.path.join(os.path.dirname(__file__), "er_diagram.png")
    plt.savefig(salida, dpi=160, bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)
    print(f"Diagrama guardado en {salida}")


if __name__ == "__main__":
    main()
