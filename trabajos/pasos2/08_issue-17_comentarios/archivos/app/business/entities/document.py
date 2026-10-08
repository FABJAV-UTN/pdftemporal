"""Entidad de dominio Document: un PDF procesado.

Objeto puro de Python, sin frameworks ni base de datos. Es lo que intercambian
los casos de uso y el repositorio.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Document:
    """Objeto de dominio que representa un PDF procesado.

    Regla de negocio: checksum y extracted_text no cambian una vez creado;
    solo filename se puede actualizar (lo hace cumplir el repositorio).

    Attributes:
        filename: Nombre original del archivo subido.
        checksum: Hash SHA-256 del contenido binario del PDF.
        extracted_text: Texto puro extraído del PDF (vacío si es escaneado).
        id: Identificador único asignado por la base de datos (None antes de persistir).
        created_at: Timestamp de creación (UTC).
        updated_at: Timestamp de última actualización (UTC).
    """

    filename: str
    checksum: str
    extracted_text: str

    id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_persisted(self) -> bool:
        """Indica si el documento ya fue guardado en la base de datos."""
        return self.id is not None