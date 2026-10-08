from abc import ABC, abstractmethod

from app.business.entities.document import Document


class IDocumentRepository(ABC):
    """Contrato de persistencia de documentos.

    Convención para "no existe": las consultas devuelven None (o False en delete);
    los casos de uso deciden si eso es un error. Un id con formato inválido se trata
    igual que uno inexistente.
    """

    @abstractmethod
    async def save(self, document: Document) -> Document:
        """Persiste un documento nuevo y lo devuelve con `id` asignado.

        Raises:
            DuplicateDocumentError: si ya existe un documento con el mismo checksum.
        """

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Document]:
        """Documentos paginados (lista vacía si no hay)."""

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Document | None:
        """El documento con ese id, o None si no existe."""

    @abstractmethod
    async def get_by_checksum(self, checksum: str) -> Document | None:
        """El documento con ese SHA-256, o None si no existe."""

    @abstractmethod
    async def update(self, document_id: str, fields: dict) -> Document | None:
        """Actualiza metadatos (hoy solo `filename`) y devuelve el documento, o None si no existe.

        checksum y extracted_text no se modifican nunca.
        """

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """True si existía y se borró, False si no existía."""
