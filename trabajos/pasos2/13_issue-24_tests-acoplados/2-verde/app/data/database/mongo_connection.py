"""Conexión a MongoDB (Motor, driver async).

Un único cliente por proceso. main.py llama a connect() al arrancar y a
disconnect() al apagar; los repositorios obtienen la base con get_database().
La URL y el nombre de la base vienen de la configuración (variables de entorno).
"""

import logging

import motor.motor_asyncio
from pymongo.errors import ConfigurationError, ConnectionFailure

from app.config.settings import settings

logger = logging.getLogger(__name__)

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_database: motor.motor_asyncio.AsyncIOMotorDatabase | None = None


async def connect() -> None:
    """Abre la conexión y verifica que el servidor responda.

    Motor conecta en forma perezosa; server_info() fuerza el handshake para
    que la app no arranque con una URL inválida.
    """
    global _client, _database

    try:
        _client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.mongo_url,
            serverSelectionTimeoutMS=5000,
        )
        await _client.server_info()
        _database = _client[settings.db_name]
        logger.info("Conexión a MongoDB establecida: %s / %s", settings.mongo_url, settings.db_name)
    except (ConnectionFailure, ConfigurationError) as exc:
        logger.error("No se pudo conectar a MongoDB: %s", exc)
        raise


async def disconnect() -> None:
    """Cierra la conexión. Después, get_database() vuelve a fallar hasta un nuevo connect()."""
    global _client, _database
    if _client:
        _client.close()
        logger.info("Conexión a MongoDB cerrada.")
    _client = None
    _database = None


def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Base de datos activa.

    Raises:
        RuntimeError: si se llama antes de connect().
    """
    if _database is None:
        raise RuntimeError("La base de datos no está inicializada. ¿Llamaste a connect()?")
    return _database
