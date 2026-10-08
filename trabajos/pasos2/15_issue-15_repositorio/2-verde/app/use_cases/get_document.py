from app.business.domain.exceptions import DocumentNotFoundError
from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository


class GetDocumentUseCase:
    def __init__(self, repository: IDocumentRepository) -> None:
        self._repository = repository

    async def execute(self, document_id: str) -> Document:
        document = await self._repository.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)
        return document
