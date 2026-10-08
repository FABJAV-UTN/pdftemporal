"""
Tests unitarios de mongo_connection.

Se reemplaza solo el driver externo (AsyncIOMotorClient) y se prueba a través
de las funciones públicas connect / get_database / disconnect, sin leer ni
escribir el estado privado del módulo.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo.errors import ConnectionFailure

from app.config.settings import settings
from app.data.database import mongo_connection

CLIENT = "app.data.database.mongo_connection.motor.motor_asyncio.AsyncIOMotorClient"


def fake_client(server_info=None) -> MagicMock:
    client = MagicMock()
    client.server_info = AsyncMock(return_value={"version": "6.0"}, side_effect=server_info)
    return client


@pytest.fixture(autouse=True)
async def start_disconnected():
    await mongo_connection.disconnect()
    yield
    await mongo_connection.disconnect()


async def test_connect_exposes_the_configured_database():
    client = fake_client()

    with patch(CLIENT, return_value=client) as client_class:
        await mongo_connection.connect()

    client_class.assert_called_once()
    assert client_class.call_args.args[0] == settings.mongo_url
    client.__getitem__.assert_called_once_with(settings.db_name)
    assert mongo_connection.get_database() is client.__getitem__.return_value


async def test_connect_fails_if_server_is_unreachable():
    client = fake_client(server_info=ConnectionFailure("Sin conexión"))

    with patch(CLIENT, return_value=client):
        with pytest.raises(ConnectionFailure):
            await mongo_connection.connect()


def test_get_database_before_connect_raises():
    with pytest.raises(RuntimeError, match="no está inicializada"):
        mongo_connection.get_database()


async def test_disconnect_closes_the_client():
    client = fake_client()
    with patch(CLIENT, return_value=client):
        await mongo_connection.connect()

    await mongo_connection.disconnect()

    client.close.assert_called_once()


async def test_after_disconnect_the_database_is_no_longer_available():
    with patch(CLIENT, return_value=fake_client()):
        await mongo_connection.connect()

    await mongo_connection.disconnect()

    with pytest.raises(RuntimeError):
        mongo_connection.get_database()


async def test_disconnect_without_connection_does_not_fail():
    await mongo_connection.disconnect()
