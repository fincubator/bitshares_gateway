import pytest
from aiohttp import web
from aiohttp.web import Application
from aiohttp.test_utils import TestClient, TestServer

from http_server import is_alive


@pytest.mark.asyncio
async def test_is_alive():
    app = Application()

    app.add_routes([web.get("/", is_alive)])

    server = TestServer(app)
    client = TestClient(server)

    await client.start_server()

    response = await client.get("/")

    assert response.status == 200
    assert await response.text() == "Ok"
