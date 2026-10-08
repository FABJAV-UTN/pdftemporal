from app.business.domain.exceptions import DocumentNotFoundError
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository


class DeleteDocumentUseCase:
    def __init__(self, repository: IDocumentRepository) -> None:
        self._repository = repository

    async def execute(self, document_id: str) -> None:
        deleted = await self._repository.delete(document_id)
        if not deleted:
            raise DocumentNotFoundError(document_id)
