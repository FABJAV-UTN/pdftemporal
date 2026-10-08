from app.business.domain.exceptions import DocumentNotFoundError
from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository


class UpdateDocumentUseCase:
    def __init__(self, repository: IDocumentRepository) -> None:
        self._repository = repository

    async def execute(self, document_id: str, fields: dict) -> Document:
        updated = await self._repository.update(document_id, fields)
        if updated is None:
            raise DocumentNotFoundError(document_id)
        return updated
