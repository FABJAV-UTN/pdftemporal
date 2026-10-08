"""La configuración se lee del entorno (12-Factor III)."""

from app.config.settings import Settings


def test_reads_values_from_environment(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb://otro-host:27017")
    monkeypatch.setenv("DB_NAME", "otra_db")
    monkeypatch.setenv("MAX_PDF_SIZE_MB", "3")

    settings = Settings(_env_file=None)

    assert settings.mongo_url == "mongodb://otro-host:27017"
    assert settings.db_name == "otra_db"
    assert settings.max_pdf_size_bytes == 3 * 1024 * 1024


def test_has_sensible_defaults(monkeypatch):
    for name in ("MONGO_URL", "DB_NAME", "MAX_PDF_SIZE_MB", "DEFAULT_PAGE_SIZE", "MAX_PAGE_SIZE", "LOG_LEVEL"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.max_pdf_size_mb == 10
    assert settings.default_page_size == 20
    assert settings.max_page_size == 100
    assert settings.log_level == "INFO"
