import logging

from aiopg.sa import SAConnection as SAConn
from sqlalchemy.sql import insert, delete, update, select
from db_utils.models import GatewayAccount, Order, BitsharesOperation


async def get_gateway_account(conn: SAConn, account_name):
    cursor = await conn.execute(select([GatewayAccount]).where(GatewayAccount.account_name == account_name).as_scalar())
    result = await cursor.fetchone()
    return result


async def update_last_operation(conn: SAConn, account_name, last_operation):
    await conn.execute(update(GatewayAccount)
                       .values(
        {GatewayAccount.last_operation: last_operation})
                       .where(GatewayAccount.account_name == account_name))


async def update_last_parsed_block(conn: SAConn, account_name, last_parsed_block):
    await conn.execute(update(GatewayAccount)
                       .values(
        {GatewayAccount.last_parsed_block: last_parsed_block})
                       .where(GatewayAccount.account_name == account_name))