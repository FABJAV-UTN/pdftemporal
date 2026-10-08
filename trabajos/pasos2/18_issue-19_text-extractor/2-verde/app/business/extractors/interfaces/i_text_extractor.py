from abc import ABC, abstractmethod


class ITextExtractor(ABC):
    """Puerto de extracción de texto de un PDF.

    El negocio depende de esta interfaz, no de una librería concreta. Hoy la
    implementa PdfplumberTextExtractor; al migrar a microservicios, un cliente
    HTTP del extractor-service implementará la misma interfaz.
    """

    @abstractmethod
    def extract(self, file_bytes: bytes) -> str:
        """Texto de todas las páginas ('' si el PDF no tiene texto seleccionable).

        Raises:
            InvalidPDFError: si el contenido no se puede leer como PDF.
        """
