import aiopg.sa
from aiopg.sa import SAConnection as SAConn, Engine
from aiopg.sa.result import RowProxy

from sqlalchemy.sql import insert, delete, update, select
from db_utils.models import GatewayWallet, BitsharesOperation
from dto import OrderType, TxStatus
from utils import get_logger

from config import pg_config


log = get_logger("Postgres")


async def init_database(**kwargs) -> Engine:
    """Async engine to execute clients requests"""
    kwargs = pg_config if not kwargs else kwargs
    engine = await aiopg.sa.create_engine(**kwargs)
    return engine


async def get_gateway_wallet(conn: SAConn, account_name: str) -> RowProxy:
    cursor = await conn.execute(
        select([GatewayWallet])
        .where(GatewayWallet.account_name == account_name)
        .as_scalar()
    )
    result = await cursor.fetchone()
    return result


async def add_gateway_wallet(conn: SAConn, **kwargs) -> bool:
    try:
        await conn.execute(insert(GatewayWallet).values(**kwargs))
        return True
    except:
        return False


async def update_last_operation(
    conn: SAConn, account_name: str, last_operation: int
) -> None:
    await conn.execute(
        update(GatewayWallet)
        .values({GatewayWallet.last_operation: last_operation})
        .where(GatewayWallet.account_name == account_name)
    )


async def update_last_parsed_block(
    conn: SAConn, account_name: str, last_parsed_block: int
) -> None:
    await conn.execute(
        update(GatewayWallet)
        .values({GatewayWallet.last_parsed_block: last_parsed_block})
        .where(GatewayWallet.account_name == account_name)
    )


async def delete_gateway_wallet(conn: SAConn, account_name: str):
    await conn.execute(
        delete(GatewayWallet).where(GatewayWallet.account_name == account_name)
    )


async def get_unconfirmed_operations(conn: SAConn):
    cursor = await conn.execute(
        select([BitsharesOperation])
        .where(BitsharesOperation.status == TxStatus.RECEIVED_NOT_CONFIRMED)
        .as_scalar()
    )
    result = await cursor.fetchall()
    return result


async def get_operation(conn: SAConn, op_id: int) -> RowProxy:
    cursor = await conn.execute(
        select([BitsharesOperation])
        .where(BitsharesOperation.op_id == op_id)
        .as_scalar()
    )
    result = await cursor.fetchone()
    return result


async def add_operation(conn: SAConn, **operation):
    isolation_level = "SERIALIZABLE"
    sql_tx = await conn.begin(isolation_level=isolation_level)
    try:
        await conn.execute(insert(BitsharesOperation).values(**operation))
        operation_db_instance = await get_operation(conn, op_id=operation["op_id"])

        if operation_db_instance.order_type is OrderType.DEPOSIT:
            account = operation_db_instance.from_account
        elif operation_db_instance.order_type == OrderType.WITHDRAWAL:
            account = operation_db_instance.to_account
        else:
            raise

        await update_last_operation(conn, account, operation["op_id"])
        await sql_tx.commit()
    except Exception as ex:
        log.exception(ex)
        print(ex)
        await sql_tx.rollback()


async def update_operation(conn: SAConn, op_id, **new_values) -> None:
    await conn.execute(
        update(BitsharesOperation)
        .values(**new_values)
        .where(BitsharesOperation.op_id == op_id)
    )
