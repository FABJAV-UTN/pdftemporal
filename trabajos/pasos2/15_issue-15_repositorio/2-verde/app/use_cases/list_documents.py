from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository


class ListDocumentsUseCase:
    def __init__(self, repository: IDocumentRepository) -> None:
        self._repository = repository

    async def execute(self, skip: int = 0, limit: int = 20) -> list[Document]:
        return await self._repository.get_all(skip=skip, limit=limit)
