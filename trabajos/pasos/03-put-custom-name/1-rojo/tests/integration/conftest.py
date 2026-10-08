"""
Fixtures compartidas por los tests de integración.

Flujo real completo: HTTP → Router → Controller → Use Case → Repositorio → MongoDB.
Requieren MongoDB corriendo (MONGO_URL) o el docker-compose.test.yml.
"""

import pytest
import pytest_asyncio
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient

from app.data.database.mongo_connection import connect, disconnect, get_database
from app.data.models.document_model import DocumentModel
from app.main import app


@pytest_asyncio.fixture
async def clean_database():
    """Conecta, inicializa Beanie y deja la colección vacía antes y después de cada test."""
    await connect()
    db = get_database()
    await init_beanie(database=db, document_models=[DocumentModel])
    await DocumentModel.delete_all()
    yield db
    await DocumentModel.delete_all()
    await disconnect()


@pytest_asyncio.fixture
async def async_client(clean_database):
    """Cliente HTTP contra la app en memoria (sin levantar servidor)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def fake_pdf_bytes() -> bytes:
    """PDF mínimo y válido de una página, sin texto."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000052 00000 n\n"
        b"0000000101 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n"
        b"147\n"
        b"%%EOF"
    )
