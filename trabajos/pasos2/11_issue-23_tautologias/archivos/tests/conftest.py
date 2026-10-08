"""
Configuración global de pytest.

Los tests de integración conectan a MongoDB real. Para no tocar los datos de
desarrollo se fuerza una base separada (pdf_test_db) ANTES de importar la app,
porque Settings lee las variables de entorno al importarse.

Para usar otra base:  DB_NAME=mi_db_test uv run pytest
"""

import os

os.environ.setdefault("DB_NAME", "pdf_test_db")
