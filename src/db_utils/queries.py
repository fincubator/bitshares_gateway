import aiopg.sa
from aiopg.sa import SAConnection as SAConn, Engine
from aiopg.sa.result import RowProxy

from sqlalchemy.sql import insert, delete, update, select
from src.db_utils.models import GatewayWallet, BitsharesOperation
from src.gw_dto import OrderType, TxStatus, TxError
from src.utils import get_logger, object_as_dict

from src.config import Config

# TODO Dependency inj
cfg = Config()

log = get_logger("Postgres")


async def init_database(cfg: Config) -> Engine:
    """Async engine to execute clients requests"""
    cfg = Config if not cfg else cfg
    engine = await aiopg.sa.create_engine(
        **{
            "host": cfg.db_host,
            "port": cfg.db_port,
            "user": cfg.db_user,
            "password": cfg.db_password,
            "database": cfg.db_database,
        }
    )
    return engine


async def get_gateway_wallet(conn: SAConn, account_name: str) -> RowProxy:
    cursor = await conn.execute(
        select([GatewayWallet])
        .where(GatewayWallet.account_name == account_name)
        .as_scalar()
    )
    result = await cursor.fetchone()
    return result


async def add_gateway_wallet(conn: SAConn, wallet: GatewayWallet) -> bool:
    try:
        _wallet = object_as_dict(wallet)
        _wallet.pop("pk")
        await conn.execute(insert(GatewayWallet).values(**_wallet))
        return True
    except Exception as ex:
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


async def insert_operation(conn: SAConn, operation: BitsharesOperation):
    _operation = object_as_dict(operation)
    _operation.pop("pk")
    await conn.execute(insert(BitsharesOperation).values(**_operation))


async def add_operation(conn: SAConn, operation: BitsharesOperation):
    isolation_level = "SERIALIZABLE"
    sql_tx = await conn.begin(isolation_level=isolation_level)
    try:
        _operation = object_as_dict(operation)
        _operation.pop("pk")
        await conn.execute(insert(BitsharesOperation).values(**_operation))
        operation_db_instance = await get_operation(conn, op_id=_operation["op_id"])

        if operation_db_instance.order_type is OrderType.DEPOSIT:
            account = operation_db_instance.from_account
        elif operation_db_instance.order_type == OrderType.WITHDRAWAL:
            account = operation_db_instance.to_account
        else:
            raise

        await update_last_operation(conn, account, operation.op_id)
        await sql_tx.commit()
    except Exception as ex:
        log.exception(ex)
        await sql_tx.rollback()


async def update_operation(
    conn: SAConn, operation: BitsharesOperation, where_key, where_value
) -> None:
    _operation = object_as_dict(operation)
    _operation.pop("pk")
    if where_key == BitsharesOperation.order_id:
        _operation.pop("order_id")
    if where_key == BitsharesOperation.op_id:
        _operation.pop("op_id")
    if where_key == BitsharesOperation.tx_hash:
        _operation.pop("tx_hash")

    q = update(BitsharesOperation).values(**_operation).where(where_key == where_value)

    await conn.execute(q)


async def get_new_ops_for_booker(conn: SAConn) -> RowProxy:
    cursor = await conn.execute(
        select([BitsharesOperation])
        .where(
            (BitsharesOperation.order_id == None)
            & (BitsharesOperation.status != TxStatus.ERROR)
        )
        .as_scalar()
    )
    result = await cursor.fetchall()
    return result


async def get_pending_operations(conn: SAConn) -> RowProxy:
    cursor = await conn.execute(
        select([BitsharesOperation])
        .where(
            (BitsharesOperation.order_id != None)
            & (BitsharesOperation.tx_hash == None)
            & (BitsharesOperation.status == TxStatus.WAIT)
        )
        .as_scalar()
    )
    result = await cursor.fetchall()
    return result


async def get_operation_by_hash(conn: SAConn, tx_hash):
    cursor = await conn.execute(
        select([BitsharesOperation])
        .where(BitsharesOperation.tx_hash == tx_hash)
        .as_scalar()
    )
    result = await cursor.fetchone()
    return result
