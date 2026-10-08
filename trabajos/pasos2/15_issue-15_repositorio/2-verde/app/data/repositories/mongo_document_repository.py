"""Implementación de IDocumentRepository sobre MongoDB (Beanie).

Traduce entre la entidad de dominio y DocumentModel, y convierte los errores
del driver en errores de dominio.
"""

import logging
from datetime import datetime, timezone

from beanie import PydanticObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository
from app.data.models.document_model import DocumentModel

logger = logging.getLogger(__name__)


class MongoDocumentRepository(IDocumentRepository):

    async def save(self, document: Document) -> Document:
        model = DocumentModel.from_entity(document)
        try:
            await model.insert()
        except DuplicateKeyError:
            # El índice único de checksum detecta duplicados que llegan al mismo tiempo.
            logger.warning("Documento duplicado: checksum=%s", document.checksum)
            raise DuplicateDocumentError(document.checksum)

        logger.info("Documento guardado id=%s", model.id)
        return model.to_entity()

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Document]:
        models = await DocumentModel.find_all().skip(skip).limit(limit).to_list()
        return [m.to_entity() for m in models]

    async def get_by_id(self, document_id: str) -> Document | None:
        model = await self._find(document_id)
        return model.to_entity() if model else None

    async def get_by_checksum(self, checksum: str) -> Document | None:
        model = await DocumentModel.find_one(DocumentModel.checksum == checksum)
        return model.to_entity() if model else None

    async def update(self, document_id: str, fields: dict) -> Document | None:
        model = await self._find(document_id)
        if model is None:
            return None

        # Solo los metadatos son modificables: checksum y texto no cambian nunca.
        changes: dict = {DocumentModel.updated_at: datetime.now(timezone.utc)}
        if "filename" in fields:
            changes[DocumentModel.name] = fields["filename"]

        await model.set(changes)
        logger.info("Documento actualizado id=%s", document_id)
        return model.to_entity()

    async def delete(self, document_id: str) -> bool:
        model = await self._find(document_id)
        if model is None:
            return False

        await model.delete()
        logger.info("Documento eliminado id=%s", document_id)
        return True

    @staticmethod
    async def _find(document_id: str) -> DocumentModel | None:
        """Busca por id; un id con formato inválido no puede existir y devuelve None."""
        try:
            object_id = PydanticObjectId(document_id)
        except (InvalidId, TypeError):
            return None
        return await DocumentModel.get(object_id)
