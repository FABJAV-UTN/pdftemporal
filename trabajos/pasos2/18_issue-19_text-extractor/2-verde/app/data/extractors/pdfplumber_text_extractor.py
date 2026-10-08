"""Adaptador de ITextExtractor con pdfplumber. Trabaja en memoria: el PDF no toca el disco."""

import io
import logging

import pdfplumber

from app.business.domain.exceptions import InvalidPDFError
from app.business.extractors.interfaces.i_text_extractor import ITextExtractor

logger = logging.getLogger(__name__)


class PdfplumberTextExtractor(ITextExtractor):

    def extract(self, file_bytes: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = [page.extract_text() or "" for page in pdf.pages]
        except Exception as exc:
            logger.warning("No se pudo leer el PDF: %s", exc)
            raise InvalidPDFError("El archivo no es un PDF válido o está dañado.") from exc

        return "\n".join(pages_text).strip()
