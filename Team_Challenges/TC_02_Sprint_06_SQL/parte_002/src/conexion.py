"""
Capa de conexión del proyecto.

El destino de producción de este TC es **Google BigQuery**. Pero BigQuery exige
credenciales de GCP que no siempre están disponibles (un compañero que aún no ha
configurado su service account, una revisión del repo en otra máquina, un CI...).
Para que los notebooks se puedan ejecutar de principio a fin en cualquier sitio,
este módulo expone una interfaz única con dos implementaciones:

    - BackendBigQuery: el destino real.
    - BackendSQLite:   un espejo local con el MISMO esquema y las MISMAS queries.

`obtener_backend()` elige automáticamente: si hay credenciales válidas usa
BigQuery, y si no cae al espejo local avisando por pantalla. Las queries de los
notebooks son SQL estándar, así que corren igual en los dos.

Diferencia importante que conviene conocer: BigQuery **no valida** claves
foráneas (las declara como informativas), mientras que SQLite sí puede hacerlo.
El espejo local activa `PRAGMA foreign_keys = ON`, así que es MÁS estricto que el
destino real: si la carga pasa en local, la integridad referencial está probada.
"""

import os
import sqlite3
from typing import Optional

import pandas as pd

from src.esquema import ORDEN_CARGA, ddl_sqlite

RUTA_SQLITE_POR_DEFECTO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "voltiatech.db"
)


class BackendSQLite:
    """Espejo local del modelo, con las claves foráneas activadas."""

    nombre = "SQLite (espejo local)"
    es_bigquery = False

    def __init__(self, ruta: str = RUTA_SQLITE_POR_DEFECTO):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        self.ruta = ruta
        self.con = sqlite3.connect(ruta)
        # SQLite trae las FK desactivadas por defecto; aquí van activadas
        self.con.execute("PRAGMA foreign_keys = ON")

    def crear_dataset(self) -> None:
        """En SQLite el 'dataset' es el propio fichero .db: no hay nada que crear."""
        return None

    def crear_tablas(self, recrear: bool = True) -> list:
        """Crea las 7 tablas en el orden que respeta las dependencias de FK."""
        creadas = []
        if recrear:
            # borra en orden inverso para no romper las FK
            for tabla in reversed(ORDEN_CARGA):
                self.con.execute(f"DROP TABLE IF EXISTS {tabla}")
        for tabla in ORDEN_CARGA:
            self.con.execute(ddl_sqlite(tabla))
            creadas.append(tabla)
        self.con.commit()
        return creadas

    def cargar(self, tabla: str, df: pd.DataFrame) -> int:
        """Inserta un DataFrame en la tabla indicada y devuelve las filas cargadas."""
        df.to_sql(tabla, self.con, if_exists="append", index=False)
        return len(df)

    def query(self, sql: str) -> pd.DataFrame:
        """Ejecuta SQL y devuelve el resultado como DataFrame."""
        return pd.read_sql_query(sql, self.con)

    def tabla(self, nombre: str) -> str:
        """Nombre cualificado de la tabla para usar en el FROM de una query."""
        return nombre

    def cerrar(self) -> None:
        self.con.close()


class BackendBigQuery:
    """Destino real: un dataset de Google BigQuery."""

    nombre = "Google BigQuery"
    es_bigquery = True

    def __init__(self, project_id: str, dataset_id: str):
        from google.cloud import bigquery

        self.bigquery = bigquery
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)

    @property
    def ref_dataset(self) -> str:
        return f"{self.project_id}.{self.dataset_id}"

    def crear_dataset(self) -> None:
        """Crea el dataset si no existe (idempotente)."""
        dataset = self.bigquery.Dataset(self.ref_dataset)
        dataset.location = "EU"  # datos de clientes europeos: región europea
        self.client.create_dataset(dataset, exists_ok=True)

    def crear_tablas(self, recrear: bool = True) -> list:
        """Crea las 7 tablas con el esquema tipado de src/esquema.py."""
        from src.esquema import schema_bigquery

        creadas = []
        for tabla in ORDEN_CARGA:
            ref = f"{self.ref_dataset}.{tabla}"
            if recrear:
                self.client.delete_table(ref, not_found_ok=True)
            t = self.bigquery.Table(ref, schema=schema_bigquery(tabla))
            self.client.create_table(t, exists_ok=True)
            creadas.append(tabla)
        return creadas

    def cargar(self, tabla: str, df: pd.DataFrame) -> int:
        """Carga un DataFrame con load_table_from_dataframe y espera al job."""
        ref = f"{self.ref_dataset}.{tabla}"
        from src.esquema import schema_bigquery

        config = self.bigquery.LoadJobConfig(
            schema=schema_bigquery(tabla),
            write_disposition="WRITE_APPEND",
        )
        job = self.client.load_table_from_dataframe(df, ref, job_config=config)
        job.result()  # bloquea hasta que termina: así los errores salen aquí
        return self.client.get_table(ref).num_rows

    def query(self, sql: str) -> pd.DataFrame:
        return self.client.query(sql).to_dataframe()

    def tabla(self, nombre: str) -> str:
        return f"`{self.ref_dataset}.{nombre}`"

    def cerrar(self) -> None:
        self.client.close()


def obtener_backend(forzar_local: bool = False, ruta_sqlite: Optional[str] = None):
    """
    Devuelve el backend a usar.

    Intenta BigQuery si hay GCP_PROJECT_ID y unas credenciales que existan en
    disco. Si falta algo, avisa y devuelve el espejo local de SQLite.

    Argumentos:
        forzar_local (bool): si es True, usa SQLite aunque haya credenciales.
        ruta_sqlite (str, opcional): ruta del fichero .db del espejo local.

    Retorna:
        BackendBigQuery o BackendSQLite.
    """
    if forzar_local:
        print("Backend: SQLite (espejo local) — forzado por el usuario.")
        return BackendSQLite(ruta_sqlite or RUTA_SQLITE_POR_DEFECTO)

    project_id = os.getenv("GCP_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID", "voltiatech")
    credenciales = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    falta = None
    if not project_id or project_id.startswith("tu-"):
        falta = "GCP_PROJECT_ID no está configurado en el .env"
    elif not credenciales or not os.path.exists(credenciales):
        falta = f"no se encuentra el fichero de credenciales ({credenciales})"

    if falta is None:
        try:
            backend = BackendBigQuery(project_id, dataset_id)
            print(f"Backend: Google BigQuery -> {backend.ref_dataset}")
            return backend
        except Exception as e:  # SDK sin instalar, credenciales inválidas...
            falta = f"{type(e).__name__}: {e}"

    print(f"Backend: SQLite (espejo local). Motivo: {falta}.")
    print("Las queries son SQL estándar: el resultado es equivalente al de BigQuery.")
    return BackendSQLite(ruta_sqlite or RUTA_SQLITE_POR_DEFECTO)
