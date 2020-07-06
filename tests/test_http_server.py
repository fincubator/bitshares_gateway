import pytest
import aiohttp

from http_server import start_http_server, http_config


@pytest.mark.asyncio
async def test_is_alive():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://{http_config['host']}:{http_config['port']}"
        ) as resp:
            assert resp.status is 200
            assert (await resp.text()) == "Ok"
