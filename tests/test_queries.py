import pytest

from db_utils.queries import *

from .fixtures import *


async def get_test_engine():
    engine = await init_database()
    return engine


@pytest.mark.asyncio
async def test_engine():
    e = await get_test_engine()
    assert isinstance(e, Engine)
    assert e.closed is False


@pytest.mark.asyncio
async def test_add_gateway_account():
    async with (await get_test_engine()).acquire() as conn:
        first_result = await add_gateway_account(conn, account_name=testnet_gateway_account)
        second_result = await add_gateway_account(conn, account_name=testnet_gateway_account)

    assert first_result
    assert second_result is False


@pytest.mark.asyncio
async def test_get_gateway_account():
    async with (await get_test_engine()).acquire() as conn:
        result: GatewayAccount = await get_gateway_account(conn, account_name=testnet_gateway_account)
    assert result
    assert testnet_gateway_account == result.account_name
    assert not result.last_operation
    assert not result.last_parsed_block


@pytest.mark.asyncio
async def test_update_last_parsed_block():
    async with (await get_test_engine()).acquire() as conn:
        await update_last_parsed_block(conn, account_name=testnet_gateway_account, last_parsed_block=666)
        result: GatewayAccount = await get_gateway_account(conn, account_name=testnet_gateway_account)
        assert result.last_parsed_block == 666
        assert isinstance(result.last_parsed_block, int)


@pytest.mark.asyncio
async def test_update_last_operation():
    async with (await get_test_engine()).acquire() as conn:
        await update_last_operation(conn, account_name=testnet_gateway_account, last_operation=13)
        result: GatewayAccount = await get_gateway_account(conn, account_name=testnet_gateway_account)
        assert result.last_operation == 13
        assert isinstance(result.last_operation, int)


@pytest.mark.asyncio
async def test_delete_gateway_account():
    async with (await get_test_engine()).acquire() as conn:
        await delete_gateway_user(conn, account_name=testnet_gateway_account)
        result = await get_gateway_account(conn, account_name=testnet_gateway_account)
        assert result is None
