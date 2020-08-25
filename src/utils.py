"""Small stand-alone utils in one place"""
import logging
import aiohttp
from aiopg.sa.result import RowProxy
from sqlalchemy import inspect


async def get_gw_settings(gw, url=""):
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


def get_logger(name: str) -> logging.Logger:

    log = logging.getLogger(name)
    log.setLevel(level=logging.INFO)
    formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    log.addHandler(ch)

    return log


def object_as_dict(obj) -> dict:
    """Represent any sqlalchemy model object as python dict"""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def rowproxy_to_dto(row_proxy: RowProxy, from_, to_):
    """Convert sqlalchemy result to Marshmallow DataTransferObject"""
    model = from_(**row_proxy)
    model_dict = object_as_dict(model)
    model_dict.pop("pk")
    instance = to_(**model_dict)
    return instance
