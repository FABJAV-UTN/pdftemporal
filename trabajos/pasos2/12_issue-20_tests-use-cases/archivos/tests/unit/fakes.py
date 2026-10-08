"""Dobles de prueba compartidos por los tests unitarios."""

from dataclasses import replace
from datetime import datetime, timezone
from itertools import count

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository

# PDF mínimo válido de una página, sin texto.
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f\n"
    b"0000000009 00000 n\n"
    b"0000000052 00000 n\n"
    b"0000000101 00000 n\n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n147\n%%EOF"
)


class InMemoryDocumentRepository(IDocumentRepository):
    """Repositorio en memoria que respeta el contrato de IDocumentRepository."""

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}
        self._ids = count(1)

    async def save(self, document: Document) -> Document:
        if await self.get_by_checksum(document.checksum) is not None:
            raise DuplicateDocumentError(document.checksum)
        saved = replace(document, id=f"{next(self._ids):024x}")
        self._documents[saved.id] = saved
        return saved

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Document]:
        return list(self._documents.values())[skip : skip + limit]

    async def get_by_id(self, document_id: str) -> Document | None:
        return self._documents.get(document_id)

    async def get_by_checksum(self, checksum: str) -> Document | None:
        return next((d for d in self._documents.values() if d.checksum == checksum), None)

    async def update(self, document_id: str, fields: dict) -> Document | None:
        document = self._documents.get(document_id)
        if document is None:
            return None
        changes = {"filename": fields["filename"]} if "filename" in fields else {}
        updated = replace(document, **changes, updated_at=datetime.now(timezone.utc))
        self._documents[document_id] = updated
        return updated

    async def delete(self, document_id: str) -> bool:
        return self._documents.pop(document_id, None) is not None
