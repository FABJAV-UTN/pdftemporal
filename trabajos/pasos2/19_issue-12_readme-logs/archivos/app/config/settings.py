"""Configuración de la aplicación (12-Factor III: config en el entorno).

Cada campo se lee de una variable de entorno con el mismo nombre en mayúsculas
(MONGO_URL, DB_NAME, MAX_PDF_SIZE_MB, ...). Ver .env.example.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PDF Extractext"
    mongo_url: str = Field("mongodb://localhost:27017")
    db_name: str = Field("pdf_extraction_db")
    max_pdf_size_mb: int = Field(10)
    default_page_size: int = Field(20)
    max_page_size: int = Field(100)
    log_level: str = Field("INFO")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def max_pdf_size_bytes(self) -> int:
        return self.max_pdf_size_mb * 1024 * 1024


settings = Settings()
