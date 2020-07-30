import pytest

from src.db_utils.queries import *
from src.config import Config
from src.utils import rowproxy_to_dto

from .fixtures import testnet_gateway_account_mock


async def get_test_engine():
    engine = await init_database(Config())
    return engine


@pytest.mark.asyncio
async def test_engine():
    e = await get_test_engine()
    assert isinstance(e, Engine)
    assert e.closed is False


@pytest.mark.asyncio
async def test_add_gateway_wallet():
    async with (await get_test_engine()).acquire() as conn:
        wallet = GatewayWallet(account_name=testnet_gateway_account_mock)

        first_result = await add_gateway_wallet(conn, wallet)
        second_result = await add_gateway_wallet(conn, wallet)

    assert first_result
    assert second_result is False


@pytest.mark.asyncio
async def test_get_gateway_wallet():
    async with (await get_test_engine()).acquire() as conn:
        result: GatewayWallet = await get_gateway_wallet(
            conn, account_name=testnet_gateway_account_mock
        )
    assert result
    assert testnet_gateway_account_mock == result.account_name
    assert not result.last_operation
    assert not result.last_parsed_block


@pytest.mark.asyncio
async def test_update_last_parsed_block():
    async with (await get_test_engine()).acquire() as conn:
        await update_last_parsed_block(
            conn, account_name=testnet_gateway_account_mock, last_parsed_block=666
        )
        result: GatewayWallet = await get_gateway_wallet(
            conn, account_name=testnet_gateway_account_mock
        )
        assert result.last_parsed_block == 666
        assert isinstance(result.last_parsed_block, int)


@pytest.mark.asyncio
async def test_update_last_operation():
    async with (await get_test_engine()).acquire() as conn:
        await update_last_operation(
            conn, account_name=testnet_gateway_account_mock, last_operation=13
        )
        gateway: GatewayWallet = await get_gateway_wallet(
            conn, account_name=testnet_gateway_account_mock
        )
        assert gateway.last_operation == 13
        assert isinstance(gateway.last_operation, int)


@pytest.mark.asyncio
async def test_add_operation():
    async with (await get_test_engine()).acquire() as conn1:
        current_op = (
            await get_gateway_wallet(conn1, account_name=testnet_gateway_account_mock)
        ).last_operation

        operation = BitsharesOperation(
            op_id=666,
            order_type=OrderType.WITHDRAWAL,
            to_account=testnet_gateway_account_mock,
        )

        await add_operation(conn1, operation)

    assert current_op
    print(current_op)

    async with (await get_test_engine()).acquire() as conn2:
        new_op = (
            await get_gateway_wallet(conn2, account_name=testnet_gateway_account_mock)
        ).last_operation
        assert new_op != current_op
        assert new_op == 666
    await conn2.execute(
        delete(BitsharesOperation).where(BitsharesOperation.op_id == 666)
    )
    await update_last_operation(conn1, testnet_gateway_account_mock, current_op)


@pytest.mark.asyncio
async def test_update_operation():
    from src.gw_dto import BitSharesOperation as BitSharesOperationDTO

    async with (await get_test_engine()).acquire() as conn:
        operation = BitsharesOperation(
            op_id=666,
            order_type=OrderType.WITHDRAWAL,
            to_account=testnet_gateway_account_mock,
        )

        await add_operation(conn, operation)

        req = await get_operation(conn, 666)
        op_dto = rowproxy_to_dto(req, BitsharesOperation, BitSharesOperationDTO)

        op_dto.status = TxStatus.RECEIVED_AND_CONFIRMED

        updated_op = BitsharesOperation(**op_dto.__dict__)
        await update_operation(conn, updated_op)
        current_value = (await get_operation(conn, 666)).status
        assert current_value == TxStatus.RECEIVED_AND_CONFIRMED

        await conn.execute(
            delete(BitsharesOperation).where(BitsharesOperation.op_id == 666)
        )


@pytest.mark.asyncio
async def test_get_unconfirmed_operations():
    async with (await get_test_engine()).acquire() as conn:
        current_unconfirmed_ops = await get_unconfirmed_operations(conn)
        assert isinstance(current_unconfirmed_ops, list)

        operation_1 = BitsharesOperation(
            op_id=666,
            order_type=OrderType.WITHDRAWAL,
            to_account=testnet_gateway_account_mock,
            status=TxStatus.RECEIVED_NOT_CONFIRMED,
        )

        await add_operation(conn, operation_1)

        operation_2 = BitsharesOperation(
            op_id=555,
            order_type=OrderType.WITHDRAWAL,
            to_account=testnet_gateway_account_mock,
            status=TxStatus.RECEIVED_AND_CONFIRMED,
        )

        await add_operation(conn, operation_2)

        operation_3 = BitsharesOperation(
            op_id=444,
            order_type=OrderType.WITHDRAWAL,
            to_account=testnet_gateway_account_mock,
            status=TxStatus.WAIT,
        )

        await add_operation(conn, operation_3)

        new_unconfirmed_ops = await get_unconfirmed_operations(conn)

        assert len(new_unconfirmed_ops) > len(current_unconfirmed_ops)

        await conn.execute(
            delete(BitsharesOperation).where(BitsharesOperation.op_id == 666)
        )
        await conn.execute(
            delete(BitsharesOperation).where(BitsharesOperation.op_id == 555)
        )
        await conn.execute(
            delete(BitsharesOperation).where(BitsharesOperation.op_id == 444)
        )


@pytest.mark.asyncio
async def test_delete_gateway_wallet():
    async with (await get_test_engine()).acquire() as conn:
        await delete_gateway_wallet(conn, account_name=testnet_gateway_account_mock)
        result = await get_gateway_wallet(
            conn, account_name=testnet_gateway_account_mock
        )
        assert result is None
