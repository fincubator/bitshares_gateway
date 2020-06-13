import logging

import aiopg.sa
from aiopg.sa import SAConnection as SAConn, Engine
from sqlalchemy.sql import insert, delete, update, select
from db_utils.models import GatewayAccount, Order, BitsharesOperation

from config import pg_config


async def init_database(**kwargs) -> Engine:
    """Async engine to execute clients requests"""
    kwargs = pg_config if not kwargs else kwargs
    engine = await aiopg.sa.create_engine(**kwargs)
    return engine


async def get_gateway_account(conn: SAConn, account_name: str):
    cursor = await conn.execute(select([GatewayAccount]).where(GatewayAccount.account_name == account_name).as_scalar())
    result = await cursor.fetchone()
    return result


async def add_gateway_account(conn: SAConn, **kwargs):
    try:
        await conn.execute(insert(GatewayAccount).values(**kwargs))
        return True
    except:
        return False


async def update_last_operation(conn: SAConn, account_name: str, last_operation: int):
    await conn.execute(update(GatewayAccount)
                       .values(
        {GatewayAccount.last_operation: last_operation})
                       .where(GatewayAccount.account_name == account_name))


async def update_last_parsed_block(conn: SAConn, account_name: str, last_parsed_block: int):
    await conn.execute(update(GatewayAccount)
                       .values(
        {GatewayAccount.last_parsed_block: last_parsed_block})
                       .where(GatewayAccount.account_name == account_name))


async def delete_gateway_user(conn: SAConn, account_name: str):
    await conn.execute(delete(GatewayAccount).where(GatewayAccount.account_name == account_name))
