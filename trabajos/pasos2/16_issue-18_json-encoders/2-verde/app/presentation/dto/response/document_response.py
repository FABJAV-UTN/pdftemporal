"""Contrato de salida de un documento: lo que recibe el cliente.

Desacopla la respuesta HTTP de la entidad y del modelo de MongoDB.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, computed_field, field_serializer

if TYPE_CHECKING:
    from app.business.entities.document import Document


class DocumentResponseDTO(BaseModel):
    id: str = Field(description="Identificador único del documento.")
    name: str = Field(description="Nombre del documento.")
    checksum: str = Field(description="Hash SHA-256 del archivo PDF.")
    extracted_text: str = Field(description="Texto extraído del PDF. Vacío si el PDF es escaneado.")
    created_at: datetime = Field(description="Fecha y hora de creación.")
    updated_at: datetime = Field(description="Fecha y hora de última modificación.")

    model_config = {"frozen": True}

    @field_serializer("created_at", "updated_at")
    def _serialize_date(self, moment: datetime) -> str:
        return moment.isoformat()

    @computed_field(return_type=str)
    @property
    def text_preview(self) -> str:
        return self.extracted_text[:500]

    @classmethod
    def from_entity(cls, document: "Document") -> "DocumentResponseDTO":
        return cls(
            id=document.id,
            name=document.filename,  # en el dominio se llama filename
            checksum=document.checksum,
            extracted_text=document.extracted_text,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )