# Kanban Etapa 1 — PDF-extractext

Equipo: **Fabio**, **Luciana** y **Celina**.

Este archivo tiene dos partes:

- **Parte 1 — Issues:** el texto para cargar en GitHub Project. No menciona archivos a copiar.
- **Parte 2 — Guía interna:** qué archivos copiar en cada issue y en qué orden. **No va en los issues.**

**Columnas sugeridas:** Backlog → To do → In progress → Review → Done.

**Reglas para todos los issues:**

- Una rama por issue: `issue-N-descripcion-corta`.
- Primero un commit `test(rojo): ...` con el test que falla, después `fix/feat/refactor(verde): ...`.
- Cada PR lo revisa otra persona del equipo antes de mergear.
- Antes de mover a Review: `uv run pytest` en verde (unitarios + integración con Mongo).

**Labels:** `bug`, `clean-code`, `tdd`, `12-factor`, `infra`, `docs`, `rendimiento`, `solid`.

---

# Parte 1 — Issues

## Primer bloque — bugs y bases (en orden)

### Issue 1 — La suite de tests corre sin configuración manual · Celina · `tdd` `infra`

Hoy `uv run pytest` falla con `ModuleNotFoundError: No module named 'app'` si no se setea `PYTHONPATH` a mano, y `Dockerfile.test` no buildea.

- [ ] `uv run pytest` funciona en un checkout limpio.
- [ ] `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests` corre toda la suite contra MongoDB.
- [ ] El README documenta los comandos correctos.

**Bloquea:** todos los demás issues.

### Issue 2 — Las excepciones de negocio no dependen de FastAPI · Luciana · `solid` `clean-code`

`app/business/domain/exceptions.py` hereda de `HTTPException`, y eso viola la regla de dependencia (DIP).

- [ ] Las excepciones de dominio son clases puras de Python, sin status codes.
- [ ] Un único traductor en la capa de presentación las convierte a RFC 9457:
  - `DocumentNotFoundError` → 404
  - `DuplicateDocumentError` → 409
  - `InvalidPDFError` → 400
  - `PDFTooLargeError` → 413
- [ ] Las respuestas de error usan `Content-Type: application/problem+json`.
- [ ] Hay una sola excepción de duplicado; se elimina el alias.
- **Depende de:** issue 1.

### Issue 3 — PUT no actualiza el nombre del documento · Fabio · `bug`

`PUT /api/v1/documents/{id}` con `{"custom_name": "x.pdf"}` devuelve 200, pero el nombre no cambia: solo se actualiza `updated_at`.

- [ ] Test de integración del PUT que falla con el bug.
- [ ] El nombre cambia y queda persistido.
- [ ] El checksum y el texto extraído no cambian.
- [ ] Un id inexistente devuelve 404.
- **Depende de:** issue 2.

### Issue 4 — Dos uploads simultáneos del mismo PDF devuelven 500 · Celina · `bug` `solid`

Si dos requests iguales pasan a la vez el chequeo de duplicados, la segunda choca con el índice único de Mongo. El repositorio lanza `ValueError` y el cliente recibe 500.

- [ ] El cliente recibe 409.
- [ ] El repositorio lanza la misma excepción de dominio que el validador (LSP).
- [ ] La interfaz `IDocumentRepository` documenta esa excepción.
- **Depende de:** issue 3 (usa sus fixtures de integración).

### Issue 5 — Un PDF dañado se guarda con texto vacío · Luciana · `bug`

Un archivo que empieza con `%PDF` pero está roto pasa la validación. El extractor se traga el error y el documento se persiste con `extracted_text = ""`.

- [ ] El cliente recibe 400 y el documento no se guarda.
- [ ] Un PDF escaneado (válido pero sin texto) se sigue aceptando.
- **Depende de:** issue 3.

### Issue 6 — El PDF se escribe en disco mientras se procesa · Fabio · `bug`

Consigna de la Etapa 1: *"El documento no debe ser persistido temporalmente mientras se procesa"*. Starlette pasa a un archivo temporal todo upload de más de 1 MB.

- [ ] Un PDF de 2 MB se procesa sin escribir nada en disco (verificado con un test).
- [ ] Una request de más de 10 MB se rechaza con 413 antes de parsear el body, también si llega sin `Content-Length` (por chunks).
- **Depende de:** issue 3.

---

## Fabio — infraestructura, 12-Factor y rendimiento

### Issue 7 — `docker-compose.yml` en la raíz · `infra` `12-factor`

- [ ] `docker compose up --build` levanta la app y MongoDB, con el puerto 8000 publicado.
- [ ] Healthcheck de Mongo y `depends_on: condition: service_healthy`.
- [ ] Sin la clave `version:`, que es obsoleta.
- [ ] Decidir si `docker-compose.dev.yml` y `docker/` siguen haciendo falta; si no, borrarlos.

### Issue 8 — Configuración consistente · `12-factor`

- [ ] `Settings` lee todo de variables de entorno con un solo nombre por valor: `MONGO_URL`, `DB_NAME`, `MAX_PDF_SIZE_MB`, `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`.
- [ ] Eliminar las 6 propiedades en MAYÚSCULAS de `Settings` (duplicación) y el campo `debug`, que no se usa.
- [ ] El router usa `DEFAULT_PAGE_SIZE` y `MAX_PAGE_SIZE` en lugar de los `20` y `100` hardcodeados.
- [ ] Tests de `Settings`: lee del entorno y tiene valores por defecto.
- El README se actualiza en el issue 12.

### Issue 9 — Limpiar dependencias · `clean-code` `infra`

- [ ] Quitar `pymupdf`, `pypdf` y `pytesseract`, que no se usan (YAGNI).
- [ ] `mongomock-motor` se queda: lo usan los tests del repositorio (issue 24).
- [ ] Declarar `pydantic-settings` en forma explícita y regenerar `uv.lock`.
- [ ] `Dockerfile` sin `tesseract-ocr`, `libtesseract-dev` ni `gcc`, y con `uv sync --no-dev` (la imagen no lleva pytest).
- [ ] Borrar `pdf_extractext.egg-info/` si está en el repo (ya está en `.gitignore`).

### Issue 10 — La extracción no bloquea el event loop · `rendimiento`

`pdfplumber` es sincrónico y corre dentro de un handler `async`, así que mientras procesa un PDF el servidor no atiende otras requests.

- [ ] Ejecutar `extract_text` con `asyncio.to_thread` (o `run_in_threadpool`) en `ProcessPDFUseCase`.
- [ ] Test: mientras se procesa un PDF lento, un `GET /documents` responde.
- **Depende de:** issue 13 (toca los mismos use cases).

### Issue 11 — CI en GitHub Actions · `tdd` `infra`

- [ ] Workflow que corra en cada PR: `uv sync`, tests unitarios y tests de integración con un `services: mongo` (imagen `mongo:6`).
- [ ] Badge en el README.

### Issue 12 — README, logs y limpieza final · `docs` `12-factor`

- [ ] README con la arquitectura real (capas + puertos y adaptadores), estructura de carpetas, variables de entorno, endpoints, errores, comandos de test y equipo.
- [ ] Badge del CI (reemplazar `OWNER/REPO` en la URL).
- [ ] Logs a stdout con nivel configurable `LOG_LEVEL` (factor XI).
- [ ] Borrar los paquetes vacíos `app/business/services/`.
- **Depende de:** todos los anteriores (el README describe el estado final).

---

## Luciana — código limpio (DRY, KISS, YAGNI, SOLID)

### Issue 13 — Eliminar el use case duplicado · `clean-code`

- [ ] Borrar `DownloadTextUseCase`, que es idéntico a `GetDocumentUseCase`, y reusar este último en el controller y en `dependencies.py`.
- [ ] Los tests de descarga siguen en verde.

### Issue 14 — Controller sin código muerto · `clean-code` `bug`

- [ ] Borrar los `try/except ...: raise` que no hacen nada (4 en `document_controller.py`).
- [ ] Sacar a funciones el armado del nombre `.txt` y del `Content-Disposition`.
- [ ] **Bug:** descargar un documento cuyo nombre tiene caracteres fuera de latin-1 (por ejemplo `informe_文件.pdf`) hace fallar la respuesta. El header debe usar `filename*=UTF-8''...` (RFC 6266).
- [ ] Mover arriba el import local de `UploadRequestDTO` en el router.

### Issue 15 — Repositorio: DRY, contrato claro y fechas en UTC · `clean-code` `solid` `bug`

- [ ] Helper privado para buscar por id (el parseo de `PydanticObjectId` está repetido 3 veces).
- [ ] `IDocumentRepository` documenta qué devuelve cada método cuando el documento no existe.
- [ ] Usar `X | None` en lugar de `Optional[X]`, y tipar los use cases con la interfaz.
- [ ] **Bug:** las fechas leídas de MongoDB vuelven sin zona horaria, mientras que las recién creadas la tienen. Siempre deben salir en UTC con zona.
- **Depende de:** issue 24 (tests del repositorio).

### Issue 16 — `pdf_validator` más simple · `clean-code`

- [ ] Borrar el fallback que lee el archivo en chunks. Con Starlette `file.size` siempre existe.
- [ ] Corregir el docstring: dice que usa `seek()` para medir y no es así.

### Issue 17 — Comentarios que mienten o sobran · `clean-code`

- [ ] Borrar `# ← agregar esto` / `# ← y esto` en `document_model.py`.
- [ ] Recortar los docstrings que explican SOLID en lugar del comportamiento: `mongo_connection.py` y `document_model.py`.
- [ ] Corregir los textos desactualizados:
  - la entidad "inmutable" (no es `frozen`);
  - la referencia a "Dev 2";
  - "12-Farctor" y "mongo_conection";
  - las menciones al "Service", que ya no existe.
- [ ] Usar indentación de 4 espacios en `dependencies.py`.

### Issue 18 — Sacar `json_encoders` (deprecado en Pydantic v2) · `clean-code`

- [ ] Reemplazarlo por `field_serializer` o por la serialización por defecto en `DocumentResponseDTO`.
- [ ] La suite corre sin warnings de Pydantic.

### Issue 19 — Puerto `TextExtractor` (prepara la migración) · `solid`

- [ ] Interfaz `ITextExtractor` en el negocio y adaptador `PdfplumberTextExtractor` en la capa de datos.
- [ ] `ProcessPDFUseCase` recibe el extractor inyectado (`dependencies.py` elige la implementación).
- [ ] Los tests de los use cases usan un extractor falso; el adaptador se prueba con PDFs reales.
- Cuando migremos a microservicios, el documents-service va a usar un `HttpTextExtractor` con la misma interfaz.
- **Depende de:** issues 10 y 13.

---

## Celina — TDD y calidad de los tests

### Issue 20 — Tests unitarios de los use cases · `tdd`

- [ ] Crear un repositorio fake en memoria que implemente `IDocumentRepository`, en `tests/unit/fakes.py`.
- [ ] Tests de `ProcessPDFUseCase`:
  - [ ] guarda con el checksum correcto;
  - [ ] un duplicado lanza `DuplicateDocumentError`;
  - [ ] un PDF corrupto lanza `InvalidPDFError` y no guarda nada.
- [ ] Tests de get, list, update y delete: el caso feliz y el caso en que no existe.
- **Depende de:** issue 13.

### Issue 21 — Fixtures de integración en un solo lugar · `tdd` `clean-code`

- [ ] Borrar `clean_database`, `async_client` y `fake_pdf_bytes` copiadas en `test_upload`, `test_delete`, `test_download`, `test_extraction` y `test_find_pdf`.
- [ ] Ya están en `tests/integration/conftest.py` (issue 3).

### Issue 22 — `pdf_validation.py` nunca se ejecutó · `tdd` `bug`

El archivo no empieza con `test_`, así que pytest lo ignora. Además tiene un `SyntaxError` (bytes con caracteres no ASCII).

- [ ] Renombrarlo a `test_pdf_validation.py`, corregir el error de sintaxis y hacer que pase.
- [ ] Quitar la aserción inerte `extracted == "" or isinstance(extracted, str)`.
- **Depende de:** issue 21.

### Issue 23 — Eliminar tautologías · `tdd`

- [ ] En `test_checksum_calculator.py`, usar hashes literales:
  - `b"hello world"` → `b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9`
  - string vacío → `e3b0c442...b855`
- [ ] Borrar `test_is_idempotent` (compara `f(x) == f(x)`) y las fixtures `known_checksum` y `sample_pdf_bytes`, que no se usan.

### Issue 24 — Tests acoplados a la implementación · `tdd` `bug`

- [ ] Reemplazar "se llamó `seek(0)`" por el comportamiento: "después de validar, el archivo se lee completo desde el inicio".
- [ ] `test_mongo_connection` usa solo `connect`, `get_database` y `disconnect`, sin leer ni escribir `_client` ni `_database`.
- [ ] **Bug:** después de `disconnect()`, `get_database()` sigue devolviendo la base cerrada. Tiene que fallar hasta un nuevo `connect()`.
- [ ] Los tests del repositorio usan `mongomock-motor` (Mongo en memoria) en lugar de mockear la cadena interna de Beanie, y verifican resultados reales (no `is not None` ni `is entity`).

### Issue 25 — Medir cobertura · `tdd`

- [ ] Agregar `pytest-cov` al grupo dev.
- [ ] `uv run pytest --cov=app` documentado en el README.
- [ ] Objetivo: más del 90 % en `app/use_cases` y `app/business`.

## Orden recomendado

**Primer lote (issues 1 a 6):**

1. Issues 1 → 2 → 3, en ese orden, uno por vez.
2. Issues 4, 5 y 6 en paralelo (Celina, Luciana y Fabio). Tocan archivos distintos.

**Segundo lote (issues 7 a 25):** en este orden, uno por vez. Varios tocan los mismos archivos, así que cada uno arranca cuando el anterior ya está mergeado.

1. Issue 7 — docker-compose.yml en la raíz (Fabio)
2. Issue 8 — Configuración consistente (Fabio)
3. Issue 9 — Limpiar dependencias (Fabio)
4. Issue 11 — CI en GitHub Actions (Fabio)
5. Issue 13 — Eliminar el use case duplicado (Luciana)
6. Issue 14 — Controller sin código muerto (Luciana)
7. Issue 16 — pdf_validator más simple (Luciana)
8. Issue 17 — Comentarios que mienten o sobran (Luciana)
9. Issue 21 — Fixtures de integración en un solo lugar (Celina)
10. Issue 22 — pdf_validation.py nunca se ejecutó (Celina)
11. Issue 23 — Eliminar tautologías (Celina)
12. Issue 20 — Tests unitarios de los use cases (Celina)
13. Issue 24 — Tests acoplados a la implementación (Celina)
14. Issue 25 — Medir cobertura (Celina)
15. Issue 15 — Repositorio: DRY, contrato claro y fechas en UTC (Luciana)
16. Issue 18 — Sacar json_encoders (deprecado en Pydantic v2) (Luciana)
17. Issue 10 — La extracción no bloquea el event loop (Fabio)
18. Issue 19 — Puerto TextExtractor (prepara la migración) (Luciana)
19. Issue 12 — README, logs y limpieza final (Fabio)

---

# Parte 2 — Guía interna: qué copiar en cada issue

> ⚠️ **Esta parte NO va en GitHub.** Es solo para el equipo.

**Dónde están los archivos:** en la carpeta `pdftemporal/pasos/`, al lado del repo temporal. Cada paso tiene su carpeta con la **misma estructura de rutas que el repo**, así que se copian tal cual en la raíz del repo oficial, pisando lo que haya.

**Cómo hacer cada issue:**

1. Crear la rama del issue a partir de `main` actualizado.
2. Copiar los archivos de `1-rojo/`.
3. Correr `uv run pytest`: **tiene que fallar** en los tests indicados.
4. Hacer el commit `test(rojo): ...`.
5. Copiar los archivos de `2-verde/`.
6. Correr `uv run pytest`: **todo en verde**.
7. Hacer el commit `fix(verde): ...`, abrir el PR y pedir review.

**Para correr los tests de integración hace falta Mongo.** Hay dos opciones:

- Usar `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests`.
- Levantar un Mongo local y correr `MONGO_URL=mongodb://localhost:27017 uv run pytest`.

> Los números de tests de cada paso salen de reproducir los pasos uno por uno sobre el código original, en el orden 1→6. Si alguien agregó tests en el medio, los totales van a variar, pero los que fallan tienen que ser los mismos.

---

### Issue 1 — Suite ejecutable (Celina)

No tiene rojo: es configuración. Carpeta: `pasos/01-suite-ejecutable/archivos/`

| Archivo | Acción |
|---|---|
| `pyproject.toml` | reemplazar |
| `Dockerfile.test` | reemplazar |
| `docker-compose.test.yml` | reemplazar |
| `README.md` | reemplazar |

**Resultado esperado:** `uv run pytest` → 95 passed.

**Commit:** `test: la suite corre sin PYTHONPATH y Dockerfile.test usa uv sync`

---

### Issue 2 — Excepciones de dominio (Luciana)

**Rojo** — `pasos/02-excepciones-dominio/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/unit/test_business/test_exceptions.py` | nuevo |
| `tests/unit/test_presentation/test_error_handlers.py` | nuevo |

**Esperado:** 2 errores de colección, porque todavía no existen `DomainError` ni `error_handlers`.

**Commit:** `test(rojo): excepciones de dominio sin FastAPI y traductor a Problem Details`

**Verde** — `pasos/02-excepciones-dominio/2-verde/`

| Archivo | Acción |
|---|---|
| `app/business/domain/exceptions.py` | reemplazar |
| `app/presentation/error_handlers.py` | nuevo |
| `app/main.py` | reemplazar (**versión intermedia**; el issue 6 la vuelve a cambiar) |
| `app/presentation/validators/pdf_validator.py` | reemplazar |
| `tests/unit/test_presentation/test_pdf_validator.py` | reemplazar |
| `tests/unit/test_presentation/test_document_controller.py` | reemplazar (**versión intermedia**; el issue 3 la vuelve a cambiar) |

**Esperado:** 107 passed.

**Commit:** `refactor(verde): excepciones de dominio puras; traducción a RFC 9457 en presentación`

---

### Issue 3 — PUT custom_name (Fabio)

**Rojo** — `pasos/03-put-custom-name/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/integration/conftest.py` | nuevo (fixtures compartidas; los issues 4, 5 y 6 las usan) |
| `tests/integration/test_update.py` | nuevo |

**Esperado:** 2 failed (`test_put_renames_the_document`, `test_put_rename_is_persisted`).

**Commit:** `test(rojo): PUT no persiste custom_name`

**Verde** — `pasos/03-put-custom-name/2-verde/`

| Archivo | Acción |
|---|---|
| `app/presentation/controllers/document_controller.py` | reemplazar |
| `tests/unit/test_presentation/test_document_controller.py` | reemplazar (versión final) |

**Esperado:** 111 passed.

**Commit:** `fix(verde): PUT traduce custom_name al campo de dominio filename`

---

### Issue 4 — Duplicado concurrente 409 (Celina)

**Rojo** — `pasos/04-duplicado-409/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/integration/test_upload_concurrency.py` | nuevo |
| `tests/unit/test_data/test_mongo_document_repository.py` | reemplazar |

**Esperado:** 2 failed (el test de integración y `test_save_lanza_error_en_duplicado`).

**Commit:** `test(rojo): un duplicado detectado por el índice único debe dar 409`

**Verde** — `pasos/04-duplicado-409/2-verde/`

| Archivo | Acción |
|---|---|
| `app/data/repositories/mongo_document_repository.py` | reemplazar |
| `app/business/repositories/interfaces/i_document_repository.py` | reemplazar |

**Esperado:** 112 passed.

**Commit:** `fix(verde): el repositorio lanza DuplicateDocumentError ante clave duplicada`

---

### Issue 5 — PDF corrupto 400 (Luciana)

**Rojo** — `pasos/05-pdf-corrupto-400/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/integration/test_upload_corrupt.py` | nuevo |
| `tests/unit/test_business/test_text_extratext.py` | reemplazar |

**Esperado:** 3 failed.

**Commit:** `test(rojo): un PDF dañado debe rechazarse con 400`

**Verde** — `pasos/05-pdf-corrupto-400/2-verde/`

| Archivo | Acción |
|---|---|
| `app/business/domain/text_extractor.py` | reemplazar |

**Esperado:** 114 passed.

**Commit:** `fix(verde): el extractor lanza InvalidPDFError si no puede leer el PDF`

---

### Issue 6 — PDF en memoria (Fabio)

**Rojo** — `pasos/06-pdf-en-memoria/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/integration/test_upload_in_memory.py` | nuevo |

**Esperado:** 2 failed (los dos detectan `rollover()` a disco).

**Commit:** `test(rojo): el PDF no debe escribirse a disco durante el procesamiento`

**Verde** — `pasos/06-pdf-en-memoria/2-verde/`

| Archivo | Acción |
|---|---|
| `app/main.py` | reemplazar (versión final) |
| `app/presentation/middlewares/__init__.py` | nuevo (vacío) |
| `app/presentation/middlewares/body_size_limit.py` | nuevo |
| `tests/unit/test_presentation/test_body_size_limit.py` | nuevo |

**Esperado:** 120 passed (83 unitarios + 37 de integración).

**Commit:** `fix(verde): el PDF se procesa en memoria; límite de body con 413 antes de parsear`

---

### Control final

Después del issue 6, el repo oficial tiene que quedar igual al repo temporal en estos 26 archivos. Los archivos ocultos (`.gitignore`, `.env.example`, `.dockerignore`, `.python-version`) **no se tocan**: el temporal no los tiene y el oficial sí.

Los issues 7 a 25 están en el segundo lote, más abajo.

---

## Segundo lote — carpeta `pasos2/`

Mismo procedimiento que el primer lote, con la carpeta `pdftemporal/pasos2/`. Las carpetas están numeradas en el orden en que hay que aplicarlas.

- Las que tienen una sola subcarpeta `archivos/` son refactors, configuración o tests nuevos: **un solo commit**, con la suite en verde.
- Las que tienen `1-rojo/` y `2-verde/` son **dos commits**, igual que en el primer lote.
- Si la carpeta del paso tiene un `BORRAR.txt`, además de copiar hay que borrar esos archivos con `git rm` (está indicado en la tabla).
- Cuando cambia `uv.lock` (issues 9 y 25), correr `uv sync` antes de los tests.

### 1. Issue 7 — `docker-compose.yml` en la raíz (Fabio)

Un solo paso — `pasos2/01_issue-07_docker-compose-raiz/archivos/`

| Archivo | Acción |
|---|---|
| `docker-compose.yml` | nuevo (versión intermedia; se vuelve a cambiar en el paso 19) |
| `docker/README_PRODUCTION.md` | reemplazar |
| `docker/app/docker-compose.yml` | reemplazar |
| `docker/mongodb/docker-compose.yml` | reemplazar |
| `docker-compose.dev.yml` | **borrar** (`git rm`) |

**Esperado:** 120 passed.

**Commit:** `infra: docker-compose.yml en la raíz con healthcheck de Mongo`

---

### 2. Issue 8 — Configuración consistente (Fabio)

Un solo paso — `pasos2/02_issue-08_configuracion/archivos/`

| Archivo | Acción |
|---|---|
| `app/config/settings.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 19) |
| `app/main.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 19) |
| `app/presentation/routers/document_router.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 6) |
| `tests/unit/test_config/test_settings.py` | nuevo (versión intermedia; se vuelve a cambiar en el paso 19) |
| `tests/unit/test_data/test_mongo_connection.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 13) |
| `tests/unit/test_presentation/test_pdf_validator.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 13) |

**Esperado:** 122 passed.

**Commit:** `refactor: configuración solo por variables de entorno, sin alias duplicados`

---

### 3. Issue 9 — Limpiar dependencias (Fabio)

Un solo paso — `pasos2/03_issue-09_dependencias/archivos/`

| Archivo | Acción |
|---|---|
| `Dockerfile` | reemplazar |
| `pyproject.toml` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 14) |
| `uv.lock` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 14) |

**Esperado:** 122 passed.

**Commit:** `build: quitar dependencias sin uso y tesseract de la imagen`

---

### 4. Issue 11 — CI en GitHub Actions (Fabio)

Un solo paso — `pasos2/04_issue-11_ci-github-actions/archivos/`

| Archivo | Acción |
|---|---|
| `.github/workflows/tests.yml` | nuevo. **Ojo:** en la carpeta del paso está como `github-workflows/tests.yml` (sin el punto, porque la herramienta no puede escribir carpetas `.github`). Copiarlo a `.github/workflows/tests.yml` en el repo. |

**Esperado:** 122 passed.

**Commit:** `ci: workflow de GitHub Actions con MongoDB`

---

### 5. Issue 13 — Eliminar el use case duplicado (Luciana)

Un solo paso — `pasos2/05_issue-13_use-case-duplicado/archivos/`

| Archivo | Acción |
|---|---|
| `app/dependencies.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 8) |
| `app/presentation/controllers/document_controller.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 6) |
| `tests/unit/test_presentation/test_document_controller.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 6) |
| `app/use_cases/download_text.py` | **borrar** (`git rm`) |

**Esperado:** 122 passed.

**Commit:** `refactor: eliminar DownloadTextUseCase duplicado; la descarga usa GetDocumentUseCase`

---

### 6. Issue 14 — Controller sin código muerto (Luciana)

**Rojo** — `pasos2/06_issue-14_controller/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/integration/test_download.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 9) |
| `tests/unit/test_presentation/test_downloads.py` | nuevo |

**Esperado:** 1 error(es) de colección (todavía no existe lo que el test importa).

**Commit:** `test(rojo): nombre de descarga .txt y header seguro para nombres no ASCII`

**Verde** — `pasos2/06_issue-14_controller/2-verde/`

| Archivo | Acción |
|---|---|
| `app/presentation/controllers/document_controller.py` | reemplazar |
| `app/presentation/downloads.py` | nuevo |
| `app/presentation/routers/document_router.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 8) |
| `tests/unit/test_presentation/test_document_controller.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 7) |

**Esperado:** 129 passed.

**Commit:** `refactor(verde): controller sin try/except muertos; descarga con nombre seguro`

---

### 7. Issue 16 — `pdf_validator` más simple (Luciana)

Un solo paso — `pasos2/07_issue-16_pdf-validator/archivos/`

| Archivo | Acción |
|---|---|
| `app/presentation/validators/pdf_validator.py` | reemplazar |
| `tests/unit/test_presentation/test_document_controller.py` | reemplazar |

**Esperado:** 129 passed.

**Commit:** `refactor: pdf_validator sin rama de respaldo imposible`

---

### 8. Issue 17 — Comentarios que mienten o sobran (Luciana)

Un solo paso — `pasos2/08_issue-17_comentarios/archivos/`

| Archivo | Acción |
|---|---|
| `app/business/domain/validators/document_validator.py` | reemplazar |
| `app/business/entities/document.py` | reemplazar |
| `app/data/database/mongo_connection.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 13) |
| `app/data/models/document_model.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 15) |
| `app/dependencies.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 18) |
| `app/presentation/routers/document_router.py` | reemplazar |

**Esperado:** 129 passed.

**Commit:** `docs: comentarios y docstrings que describen el código actual`

---

### 9. Issue 21 — Fixtures de integración en un solo lugar (Celina)

Un solo paso — `pasos2/09_issue-21_fixtures-integracion/archivos/`

| Archivo | Acción |
|---|---|
| `tests/integration/conftest.py` | reemplazar |
| `tests/integration/pdf_validation.py` | reemplazar |
| `tests/integration/test_delete.py` | reemplazar |
| `tests/integration/test_download.py` | reemplazar |
| `tests/integration/test_extraction.py` | reemplazar |
| `tests/integration/test_find_pdf.py` | reemplazar |
| `tests/integration/test_upload.py` | reemplazar |
| `tests/integration/test_upload_in_memory.py` | reemplazar |

**Esperado:** 129 passed.

**Commit:** `test: fixtures de integración centralizadas en conftest`

---

### 10. Issue 22 — `pdf_validation.py` nunca se ejecutó (Celina)

Un solo paso — `pasos2/10_issue-22_test-pdf-validation/archivos/`

| Archivo | Acción |
|---|---|
| `tests/integration/test_pdf_validation.py` | nuevo |
| `tests/integration/pdf_validation.py` | **borrar** (`git rm`) |

**Esperado:** 144 passed.

**Commit:** `test: test_pdf_validation.py se ejecuta y refleja el comportamiento actual`

---

### 11. Issue 23 — Eliminar tautologías (Celina)

Un solo paso — `pasos2/11_issue-23_tautologias/archivos/`

| Archivo | Acción |
|---|---|
| `tests/conftest.py` | reemplazar |
| `tests/unit/test_business/test_checksum_calculator.py` | reemplazar |

**Esperado:** 142 passed.

**Commit:** `test: valores esperados independientes del código; sin fixtures muertas`

---

### 12. Issue 20 — Tests unitarios de los use cases (Celina)

Un solo paso — `pasos2/12_issue-20_tests-use-cases/archivos/`

| Archivo | Acción |
|---|---|
| `tests/unit/fakes.py` | nuevo (versión intermedia; se vuelve a cambiar en el paso 18) |
| `tests/unit/test_use_cases/test_document_crud.py` | nuevo (versión intermedia; se vuelve a cambiar en el paso 18) |
| `tests/unit/test_use_cases/test_process_pdf.py` | nuevo (versión intermedia; se vuelve a cambiar en el paso 18) |

**Esperado:** 155 passed.

**Commit:** `test: tests unitarios de los casos de uso con repositorio en memoria`

---

### 13. Issue 24 — Tests acoplados a la implementación (Celina)

**Rojo** — `pasos2/13_issue-24_tests-acoplados/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/unit/test_data/test_mongo_connection.py` | reemplazar |

**Esperado:** 2 failed.

**Commit:** `test(rojo): tras disconnect la base ya no está disponible`

**Verde** — `pasos2/13_issue-24_tests-acoplados/2-verde/`

| Archivo | Acción |
|---|---|
| `app/data/database/mongo_connection.py` | reemplazar |
| `tests/unit/test_data/test_mongo_document_repository.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 15) |
| `tests/unit/test_presentation/test_pdf_validator.py` | reemplazar |

**Esperado:** 161 passed.

**Commit:** `fix(verde): disconnect limpia el estado; tests de repositorio con mongomock y sin detalles internos`

---

### 14. Issue 25 — Medir cobertura (Celina)

Un solo paso — `pasos2/14_issue-25_cobertura/archivos/`

| Archivo | Acción |
|---|---|
| `pyproject.toml` | reemplazar |
| `uv.lock` | reemplazar |

**Esperado:** 161 passed.

**Commit:** `test: medición de cobertura con pytest-cov`

---

### 15. Issue 15 — Repositorio: DRY, contrato claro y fechas en UTC (Luciana)

**Rojo** — `pasos2/15_issue-15_repositorio/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/unit/test_data/test_mongo_document_repository.py` | reemplazar |

**Esperado:** 2 failed.

**Commit:** `test(rojo): las fechas leídas de la base vienen sin zona horaria`

**Verde** — `pasos2/15_issue-15_repositorio/2-verde/`

| Archivo | Acción |
|---|---|
| `app/business/repositories/interfaces/i_document_repository.py` | reemplazar |
| `app/data/models/document_model.py` | reemplazar |
| `app/data/repositories/mongo_document_repository.py` | reemplazar |
| `app/use_cases/delete_document.py` | reemplazar |
| `app/use_cases/get_document.py` | reemplazar |
| `app/use_cases/list_documents.py` | reemplazar |
| `app/use_cases/process_pdf.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 17) |
| `app/use_cases/update_document.py` | reemplazar |

**Esperado:** 163 passed.

**Commit:** `refactor(verde): repositorio sin código repetido, contrato documentado y fechas en UTC`

---

### 16. Issue 18 — Sacar `json_encoders` (deprecado en Pydantic v2) (Luciana)

**Rojo** — `pasos2/16_issue-18_json-encoders/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/unit/test_presentation/test_document_response.py` | nuevo |

**Esperado:** 1 failed.

**Commit:** `test(rojo): DocumentResponseDTO no debe usar json_encoders (deprecado)`

**Verde** — `pasos2/16_issue-18_json-encoders/2-verde/`

| Archivo | Acción |
|---|---|
| `app/presentation/dto/response/document_response.py` | reemplazar |

**Esperado:** 165 passed.

**Commit:** `refactor(verde): fechas serializadas con field_serializer en lugar de json_encoders`

---

### 17. Issue 10 — La extracción no bloquea el event loop (Fabio)

**Rojo** — `pasos2/17_issue-10_event-loop/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/unit/test_use_cases/test_process_pdf_concurrency.py` | nuevo (versión intermedia; se vuelve a cambiar en el paso 18) |

**Esperado:** 1 failed.

**Commit:** `test(rojo): la extracción bloquea el event loop`

**Verde** — `pasos2/17_issue-10_event-loop/2-verde/`

| Archivo | Acción |
|---|---|
| `app/use_cases/process_pdf.py` | reemplazar (versión intermedia; se vuelve a cambiar en el paso 18) |

**Esperado:** 166 passed.

**Commit:** `perf(verde): extracción en un hilo para no bloquear el event loop`

---

### 18. Issue 19 — Puerto `TextExtractor` (prepara la migración) (Luciana)

**Rojo** — `pasos2/18_issue-19_text-extractor/1-rojo/`

| Archivo | Acción |
|---|---|
| `tests/unit/fakes.py` | reemplazar |
| `tests/unit/test_data/test_pdfplumber_text_extractor.py` | nuevo |
| `tests/unit/test_use_cases/test_document_crud.py` | reemplazar |
| `tests/unit/test_use_cases/test_process_pdf.py` | reemplazar |
| `tests/unit/test_use_cases/test_process_pdf_concurrency.py` | reemplazar |

**Esperado:** 4 error(es) de colección (todavía no existe lo que el test importa).

**Commit:** `test(rojo): ProcessPDFUseCase recibe el extractor de texto inyectado`

**Verde** — `pasos2/18_issue-19_text-extractor/2-verde/`

| Archivo | Acción |
|---|---|
| `app/business/extractors/__init__.py` | nuevo |
| `app/business/extractors/interfaces/__init__.py` | nuevo |
| `app/business/extractors/interfaces/i_text_extractor.py` | nuevo |
| `app/data/extractors/__init__.py` | nuevo |
| `app/data/extractors/pdfplumber_text_extractor.py` | nuevo |
| `app/dependencies.py` | reemplazar |
| `app/use_cases/process_pdf.py` | reemplazar |
| `app/business/domain/text_extractor.py` | **borrar** (`git rm`) |
| `tests/unit/test_business/test_text_extratext.py` | **borrar** (`git rm`) |

**Esperado:** 166 passed.

**Commit:** `refactor(verde): puerto ITextExtractor y adaptador pdfplumber en la capa de datos`

---

### 19. Issue 12 — README, logs y limpieza final (Fabio)

Un solo paso — `pasos2/19_issue-12_readme-logs/archivos/`

| Archivo | Acción |
|---|---|
| `.env.example` | reemplazar |
| `README.md` | reemplazar |
| `app/config/settings.py` | reemplazar |
| `app/main.py` | reemplazar |
| `app/use_cases/__init__.py` | nuevo |
| `docker-compose.yml` | reemplazar |
| `tests/unit/test_config/test_settings.py` | reemplazar |
| `app/business/services/interfaces/__init__.py` | **borrar** (`git rm`) |
| `app/business/services/__init__.py` | **borrar** (`git rm`) |

**Esperado:** 166 passed.

**Commit:** `docs: README con la arquitectura actual; logs a stdout; sin paquetes vacíos`

---

### Control final del segundo lote

- Después del paso 19, el repo tiene que quedar igual a la suma de los dos lotes: **166 tests** en verde (los números salen de aplicar los pasos en orden sobre el resultado del primer lote).
- Borrar también la carpeta vacía `app/business/services/` si quedó (git no guarda carpetas vacías).
- En el `README.md`, reemplazar `OWNER/REPO` en la URL del badge por el repo oficial.
- Correr una vez todo contra Mongo real: `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests`, y levantar la app con `docker compose up --build` para probarla en `/docs`.
