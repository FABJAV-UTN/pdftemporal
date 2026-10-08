# 📄 PDF-extractext

> API REST que recibe archivos PDF, extrae su texto y lo guarda en MongoDB junto con el checksum del archivo, con CRUD completo sobre los documentos.

![tests](https://github.com/OWNER/REPO/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-6-47A248?style=flat-square&logo=mongodb&logoColor=white)
![uv](https://img.shields.io/badge/uv-gestor_de_paquetes-DE5FE9?style=flat-square)

Proyecto de la materia **Desarrollo de Software** — UTN Facultad Regional San Rafael, 2026 (Etapa 1).

---

## Contenido

- [Funcionalidades](#funcionalidades)
- [Arquitectura](#arquitectura)
- [Configuración](#configuración)
- [Cómo levantarlo](#cómo-levantarlo)
- [Endpoints](#endpoints)
- [Tests](#tests)
- [Principios aplicados](#principios-aplicados)
- [Equipo](#equipo)

---

## Funcionalidades

- **Subir un PDF** (`multipart/form-data`) y extraer solo su texto.
- **Persistir** el texto en MongoDB con el **checksum SHA-256** del archivo.
- **CRUD** de los documentos: listar (paginado), consultar, renombrar, borrar y descargar el texto como `.txt`.
- **Validación** de formato (magic bytes `%PDF` y que el contenido se pueda leer) y de tamaño (`MAX_PDF_SIZE_MB`).
- **Sin archivos temporales**: el PDF se procesa en memoria, nunca se escribe en disco.
- **Sin duplicados**: el mismo contenido no se guarda dos veces, aunque llegue en dos requests simultáneas (índice único en `checksum`).
- **Errores en formato RFC 9457** (Problem Details), con `Content-Type: application/problem+json`.

---

## Arquitectura

Capas con dependencias hacia adentro: el negocio no conoce FastAPI, MongoDB ni pdfplumber, solo interfaces (puertos).

```
          HTTP
           │
┌──────────▼───────────────────────────────────────────────┐
│ PRESENTACIÓN  routers · controller · DTOs · validador    │
│               middleware de tamaño · errores → RFC 9457  │
└──────────┬───────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────┐
│ CASOS DE USO  ProcessPDF · List · Get · Update · Delete  │
└──────────┬───────────────────────────────────────────────┘
           │ dependen de
┌──────────▼───────────────────────────────────────────────┐
│ NEGOCIO       entidad Document · checksum · reglas       │
│               excepciones de dominio                     │
│               puertos: IDocumentRepository, ITextExtractor│
└──────────▲───────────────────────────────────────────────┘
           │ implementan
┌──────────┴───────────────────────────────────────────────┐
│ DATOS         MongoDocumentRepository (Beanie/MongoDB)   │
│               PdfplumberTextExtractor                    │
└──────────────────────────────────────────────────────────┘
```

`app/dependencies.py` es la raíz de composición: es el único lugar que elige las implementaciones concretas.

### Estructura

```
app/
├── main.py                     # App FastAPI: logging, middleware, errores, router
├── dependencies.py             # Composición (inyección de dependencias)
├── config/settings.py          # Configuración desde variables de entorno
├── presentation/
│   ├── routers/                # Endpoints HTTP
│   ├── controllers/            # DTOs ↔ casos de uso
│   ├── dto/                    # Contratos de entrada y salida
│   ├── validators/             # Formato y tamaño del PDF
│   ├── middlewares/            # Límite de tamaño del body (413)
│   ├── error_handlers.py       # Errores de dominio → RFC 9457
│   └── downloads.py            # Nombre y header de la descarga .txt
├── use_cases/                  # Un caso de uso por operación
├── business/
│   ├── entities/               # Document
│   ├── domain/                 # checksum, reglas, excepciones
│   ├── repositories/interfaces # Puerto IDocumentRepository
│   └── extractors/interfaces   # Puerto ITextExtractor
└── data/
    ├── database/               # Conexión a MongoDB
    ├── models/                 # DocumentModel (Beanie)
    ├── repositories/           # MongoDocumentRepository
    └── extractors/             # PdfplumberTextExtractor
tests/
├── unit/                       # Sin servicios externos
└── integration/                # HTTP → MongoDB real
```

---

## Configuración

Todo se configura con variables de entorno (12-Factor III). Ver `.env.example`.

| Variable | Por defecto | Descripción |
|---|---|---|
| `MONGO_URL` | `mongodb://localhost:27017` | URL de MongoDB |
| `DB_NAME` | `pdf_extraction_db` | Base de datos |
| `MAX_PDF_SIZE_MB` | `10` | Tamaño máximo del PDF |
| `DEFAULT_PAGE_SIZE` | `20` | Documentos por página si no se indica `limit` |
| `MAX_PAGE_SIZE` | `100` | Máximo permitido para `limit` |
| `LOG_LEVEL` | `INFO` | Nivel de logs (salen por stdout) |

---

## Cómo levantarlo

### Con Docker (recomendado)

```bash
cp .env.example .env      # opcional: todas las variables tienen valor por defecto
docker compose up --build
```

La API queda en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`.

> En Linux, si aparece `permission denied ... docker.sock`: `sudo usermod -aG docker $USER` y luego `newgrp docker`.

### Sin Docker

Requiere Python 3.12, [uv](https://docs.astral.sh/uv/) y un MongoDB local.

```bash
uv sync
MONGO_URL=mongodb://localhost:27017 uv run fastapi dev app/main.py
```

---

## Endpoints

Base: `/api/v1/documents`

| Método | Ruta | Descripción | Respuesta OK |
|---|---|---|---|
| `POST` | `/` | Sube un PDF (`file`, y `custom_name` opcional) | `201` documento creado |
| `GET` | `/?skip=0&limit=20` | Lista paginada | `200` lista |
| `GET` | `/{id}` | Un documento | `200` documento |
| `PUT` | `/{id}` | Renombra: `{"custom_name": "nuevo.pdf"}` | `200` documento |
| `DELETE` | `/{id}` | Borra | `200` mensaje |
| `GET` | `/{id}/download` | Descarga el texto como `.txt` | `200` archivo |

Ejemplo de documento:

```json
{
  "id": "664f2a1b3e8c1a2b3c4d5e6f",
  "name": "informe-final.pdf",
  "checksum": "a3f1d29e…",
  "extracted_text": "Contenido del PDF…",
  "text_preview": "Contenido del PDF…",
  "created_at": "2026-05-23T10:30:00+00:00",
  "updated_at": "2026-05-23T10:30:00+00:00"
}
```

### Errores

| Status | Cuándo |
|---|---|
| `400` | No es un PDF (magic bytes) o su contenido no se puede leer |
| `404` | El documento no existe |
| `409` | Ya existe un documento con el mismo contenido (checksum) |
| `413` | El archivo supera `MAX_PDF_SIZE_MB` |
| `422` | Parámetros inválidos (validación de FastAPI) |

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Document '664f…' not found.",
  "instance": "http://localhost:8000/api/v1/documents/664f…"
}
```

---

## Tests

Desarrollados con **TDD**: cada cambio arranca con un test que falla (`test(rojo): …`) y sigue con el código que lo hace pasar (`fix/feat(verde): …`).

```bash
# Unitarios (no necesitan MongoDB)
uv run pytest tests/unit

# Integración (necesitan MongoDB en MONGO_URL)
MONGO_URL=mongodb://localhost:27017 uv run pytest tests/integration

# Todo dentro de Docker, con su propia base
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests

# Cobertura
uv run pytest --cov
```

Los tests de integración usan una base separada (`pdf_test_db`) para no tocar los datos de desarrollo. El workflow `.github/workflows/tests.yml` corre toda la suite en cada push y pull request.

---

## Principios aplicados

- **Arquitectura limpia / puertos y adaptadores**: el negocio depende de interfaces; las implementaciones se eligen en `dependencies.py`.
- **SOLID**: un caso de uso por operación (S), nuevos repositorios o extractores sin tocar el negocio (O), implementaciones intercambiables (L), interfaces chicas (I), dependencias invertidas (D).
- **DRY, KISS, YAGNI**: sin dependencias ni capas que no se usen.
- **TDD**: historial rojo → verde por cada cambio.
- **12-Factor**: un repo (I), dependencias declaradas y fijadas con `uv.lock` (II), configuración por entorno (III), MongoDB como servicio externo (IV), build/run separados con Docker (V), procesos sin estado (VI), port binding (VII), logs a stdout (XI).

---

## Equipo

- Fabio
- Luciana
- Celina

---

## Licencia

MIT — ver [LICENSE](LICENSE).
