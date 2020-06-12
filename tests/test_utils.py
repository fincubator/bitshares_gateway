import pytest

from utils import get_gw_settings

from .fixtures import test_control_center_url


@pytest.mark.asyncio
async def test_get_gw_settings():
    settings = await get_gw_settings("BTC", test_control_center_url)
    assert isinstance(settings, dict)