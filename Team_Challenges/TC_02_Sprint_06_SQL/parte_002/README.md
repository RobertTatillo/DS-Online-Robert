# Team Challenge SQL

## Parte 1: SQL Murder Mystery
## Parte 2: Diseño e implementación de base de datos en BigQuery

---

## Estructura del repositorio

```
tc-sql/
├── parte1/
│   └── sql_murder_mystery.ipynb
├── parte2/
│   ├── bigquery_setup.ipynb
│   ├── docs/
│   │   └── er_diagram.png          ← diagrama ER (a completar)
│   └── requirements.txt
├── .env.example                    ← plantilla de variables de entorno
├── .gitignore
└── README.md
```

## Setup

### 1. Clonar el repositorio
```bash
git clone https://github.com/[usuario]/tc-sql.git
cd tc-sql
```

### 2. Crear el entorno virtual
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows
```

### 3. Instalar dependencias
```bash
pip install -r parte2/requirements.txt
```

### 4. Configurar credenciales
```bash
cp .env.example .env
# Editar .env con vuestros valores reales
```

El fichero `.env` **nunca se sube al repositorio**.

### 5. Credenciales de Google Cloud

Dos opciones:
- **Service Account**: descargad el JSON desde IAM → Service Accounts y apuntad la ruta en `GOOGLE_APPLICATION_CREDENTIALS`
- **Application Default Credentials**: `gcloud auth application-default login`

---

## Equipo

| Nombre | Rol | Rama |
|--------|-----|------|
| ... | Scrum Master | feature/setup-bigquery |
| ... | Data Modeler | feature/er-diagram |
| ... | Data Engineer | feature/data-generation |
| ... | QA / Docs | feature/queries-validation |

---

## Presentación — Sprint 8

- Duración total: **10 minutos** (ambas partes)
- Lugar: sesión Team Challenge Sprint 8
