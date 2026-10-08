"""Modelo de persistencia de un documento en MongoDB (Beanie).

Vive solo en la capa de datos: el resto de la aplicación trabaja con la
entidad de dominio `Document`. La conversión entre ambos está acá, en un
único lugar (to_entity / from_entity).
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from beanie import Document
from pydantic import Field
from pymongo import IndexModel

if TYPE_CHECKING:
    from app.business.entities.document import Document as DocumentEntity


class DocumentModel(Document):
    """Documento guardado en la colección `documents`.

    `name` es el nombre visible del archivo; en el dominio se llama `filename`.
    El índice único sobre `checksum` impide duplicados aun con uploads simultáneos.
    """

    name: str
    checksum: str
    extracted_text: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "documents"
        is_root = True
        indexes = [IndexModel([("checksum", 1)], unique=True)]

    def to_entity(self) -> "DocumentEntity":
        from app.business.entities.document import Document as DocumentEntity

        return DocumentEntity(
            id=str(self.id) if self.id else None,
            filename=self.name,
            checksum=self.checksum,
            extracted_text=self.extracted_text,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: "DocumentEntity") -> "DocumentModel":
        return cls(
            name=entity.filename,
            checksum=entity.checksum,
            extracted_text=entity.extracted_text,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
