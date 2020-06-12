import aiohttp

from config import CONTROLCENTERURL


async def get_gw_settings(gw, url=CONTROLCENTERURL):
    """Fetch gateway settings from control_center. Control_center URL stored in config/const.py"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            try:
                json = await resp.json()
                for gw_settings in json:
                    if gw_settings["name"] == gw:
                        return gw_settings
            except Exception as ex:
                raise Exception(f"Unable to fetch gateway {gw} settings: {ex}")
