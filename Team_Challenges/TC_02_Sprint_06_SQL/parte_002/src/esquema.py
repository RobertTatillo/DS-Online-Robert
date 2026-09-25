"""
Definición única del modelo de datos de VoltiaTech.

Este módulo es la fuente de verdad del esquema: lo importan los tres notebooks
(setup, generación y verificación) para que no puedan desincronizarse entre sí.

Cada tabla se describe con sus campos, el tipo BigQuery, el modo (REQUIRED /
NULLABLE), si es clave primaria o foránea, y una descripción. De aquí se derivan
automáticamente tanto los esquemas de BigQuery como el DDL de SQLite del
espejo local.
"""

from typing import Dict, List

# Mapeo de tipos BigQuery -> SQLite, para poder montar el espejo local
TIPOS_SQLITE = {
    "STRING": "TEXT",
    "INT64": "INTEGER",
    "NUMERIC": "REAL",
    "FLOAT64": "REAL",
    "BOOL": "INTEGER",
    "DATE": "TEXT",
    "TIMESTAMP": "TEXT",
}

# Estructura: (nombre_campo, tipo_bq, modo, clave, descripcion)
#   clave = "PK" | "FK -> tabla.campo" | ""
ESQUEMA: Dict[str, List[tuple]] = {

    # -----------------------------------------------------------------------
    "categories": [
        ("category_id",   "INT64",  "REQUIRED", "PK", "Identificador de la categoría"),
        ("category_name", "STRING", "REQUIRED", "",   "Nombre de la categoría"),
        ("description",   "STRING", "NULLABLE", "",   "Descripción libre"),
    ],

    # -----------------------------------------------------------------------
    "customers": [
        ("customer_id",         "INT64",  "REQUIRED", "PK", "Identificador del cliente"),
        ("first_name",          "STRING", "REQUIRED", "",   "Nombre"),
        ("last_name",           "STRING", "REQUIRED", "",   "Apellido"),
        ("email",               "STRING", "REQUIRED", "",   "Email de contacto (único)"),
        ("country",             "STRING", "REQUIRED", "",   "País de residencia"),
        ("city",                "STRING", "REQUIRED", "",   "Ciudad de residencia"),
        ("acquisition_channel", "STRING", "REQUIRED", "",   "Canal de captación"),
        ("registered_at",       "DATE",   "REQUIRED", "",   "Fecha de alta"),
    ],

    # -----------------------------------------------------------------------
    "products": [
        ("product_id",   "INT64",   "REQUIRED", "PK",                      "Identificador del producto"),
        ("product_name", "STRING",  "REQUIRED", "",                        "Nombre comercial"),
        ("category_id",  "INT64",   "REQUIRED", "FK -> categories.category_id", "Categoría a la que pertenece"),
        ("price",        "NUMERIC", "REQUIRED", "",                        "Precio de venta actual (EUR)"),
        ("cost",         "NUMERIC", "REQUIRED", "",                        "Coste de adquisición (EUR)"),
        ("stock",        "INT64",   "REQUIRED", "",                        "Unidades disponibles"),
        ("is_active",    "BOOL",    "REQUIRED", "",                        "Si sigue en catálogo"),
    ],

    # -----------------------------------------------------------------------
    "orders": [
        ("order_id",          "INT64",  "REQUIRED", "PK",                       "Identificador del pedido"),
        ("customer_id",       "INT64",  "REQUIRED", "FK -> customers.customer_id", "Cliente que realiza el pedido"),
        ("status",            "STRING", "REQUIRED", "",                         "pending/confirmed/shipped/delivered/cancelled/returned"),
        ("shipping_country",  "STRING", "REQUIRED", "",                         "País de envío"),
        ("shipping_city",     "STRING", "REQUIRED", "",                         "Ciudad de envío"),
        ("ordered_at",        "DATE",   "REQUIRED", "",                         "Fecha del pedido"),
        ("shipped_at",        "DATE",   "NULLABLE", "",                         "Fecha de envío (null si aún no salió)"),
        ("delivered_at",      "DATE",   "NULLABLE", "",                         "Fecha de entrega (null si no se entregó)"),
    ],

    # -----------------------------------------------------------------------
    "order_items": [
        ("order_item_id", "INT64",   "REQUIRED", "PK",                      "Identificador de la línea"),
        ("order_id",      "INT64",   "REQUIRED", "FK -> orders.order_id",   "Pedido al que pertenece"),
        ("product_id",    "INT64",   "REQUIRED", "FK -> products.product_id", "Producto vendido"),
        ("quantity",      "INT64",   "REQUIRED", "",                        "Unidades de ese producto"),
        ("unit_price",    "NUMERIC", "REQUIRED", "",                        "Precio unitario EN EL MOMENTO de la compra"),
        ("discount_pct",  "NUMERIC", "REQUIRED", "",                        "Descuento aplicado a la línea (0-100)"),
    ],

    # -----------------------------------------------------------------------
    "payments": [
        ("payment_id",     "INT64",   "REQUIRED", "PK",                    "Identificador del pago"),
        ("order_id",       "INT64",   "REQUIRED", "FK -> orders.order_id", "Pedido pagado"),
        ("payment_method", "STRING",  "REQUIRED", "",                      "card/paypal/bank_transfer/bizum"),
        ("payment_status", "STRING",  "REQUIRED", "",                      "completed/pending/refunded/failed"),
        ("amount",         "NUMERIC", "REQUIRED", "",                      "Importe cobrado (EUR)"),
        ("paid_at",        "DATE",    "NULLABLE", "",                      "Fecha del cobro (null si pendiente o fallido)"),
    ],

    # -----------------------------------------------------------------------
    "reviews": [
        ("review_id",     "INT64",  "REQUIRED", "PK",                              "Identificador de la valoración"),
        ("order_item_id", "INT64",  "REQUIRED", "FK -> order_items.order_item_id", "Línea de pedido valorada"),
        ("rating",        "INT64",  "REQUIRED", "",                                "Puntuación de 1 a 5"),
        ("comment",       "STRING", "NULLABLE", "",                                "Comentario libre (opcional)"),
        ("created_at",    "DATE",   "REQUIRED", "",                                "Fecha de la valoración"),
    ],
}

# Orden de creación y de carga: respeta las dependencias de claves foráneas.
# categories y customers no dependen de nadie; reviews depende de order_items,
# que a su vez depende de orders y products.
ORDEN_CARGA = [
    "categories",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "reviews",
]


def campos(tabla: str) -> List[str]:
    """Devuelve la lista de nombres de campo de una tabla, en orden."""
    return [c[0] for c in ESQUEMA[tabla]]


def clave_primaria(tabla: str) -> str:
    """Devuelve el nombre del campo marcado como PK."""
    for nombre, _, _, clave, _ in ESQUEMA[tabla]:
        if clave == "PK":
            return nombre
    raise KeyError(f"La tabla '{tabla}' no tiene PK declarada.")


def foraneas(tabla: str) -> List[tuple]:
    """Devuelve [(campo, tabla_destino, campo_destino), ...] de esa tabla."""
    salida = []
    for nombre, _, _, clave, _ in ESQUEMA[tabla]:
        if clave.startswith("FK"):
            destino = clave.split("->")[1].strip()
            tabla_destino, campo_destino = destino.split(".")
            salida.append((nombre, tabla_destino, campo_destino))
    return salida


def schema_bigquery(tabla: str):
    """
    Construye la lista de bigquery.SchemaField de una tabla.

    Se importa google.cloud aquí dentro y no arriba para que el módulo siga
    siendo utilizable sin tener instalado el SDK de BigQuery (por ejemplo,
    cuando solo se trabaja con el espejo local de SQLite).
    """
    from google.cloud import bigquery

    return [
        bigquery.SchemaField(nombre, tipo, mode=modo, description=desc)
        for nombre, tipo, modo, _, desc in ESQUEMA[tabla]
    ]


def ddl_sqlite(tabla: str) -> str:
    """
    Genera el CREATE TABLE de SQLite equivalente al esquema de BigQuery.

    BigQuery no impone claves foráneas (no las valida), pero SQLite sí puede
    hacerlo. Por eso el espejo local es más estricto que el destino real: si la
    carga pasa en SQLite con las FK activadas, la integridad referencial del
    modelo está garantizada.
    """
    lineas = []
    for nombre, tipo, modo, clave, _ in ESQUEMA[tabla]:
        sql_tipo = TIPOS_SQLITE[tipo]
        restriccion = " NOT NULL" if modo == "REQUIRED" else ""
        if clave == "PK":
            restriccion = " PRIMARY KEY"
        lineas.append(f"    {nombre} {sql_tipo}{restriccion}")

    for campo, tabla_destino, campo_destino in foraneas(tabla):
        lineas.append(f"    FOREIGN KEY ({campo}) REFERENCES {tabla_destino}({campo_destino})")

    cuerpo = ",\n".join(lineas)
    return f"CREATE TABLE {tabla} (\n{cuerpo}\n);"


def resumen() -> str:
    """Devuelve un resumen legible del modelo completo."""
    filas = []
    for tabla in ORDEN_CARGA:
        fks = foraneas(tabla)
        filas.append(
            f"{tabla:<14} {len(ESQUEMA[tabla]):>2} campos | PK: {clave_primaria(tabla):<14}"
            f" | FKs: {', '.join(f[0] for f in fks) if fks else '-'}"
        )
    return "\n".join(filas)
