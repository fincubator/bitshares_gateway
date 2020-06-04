import pytest

from bitshares_utils import *

from .fixtures import *


@pytest.mark.asyncio
async def test_init_bitshares():
    instance = await init_bitshares(account=testnet_gateway_account,
                                    node=testnet_bitshares_nodes,
                                    keys=[testnet_gateway_active, testnet_gateway_memo])
    shared_instance = shared_bitshares_instance()

    assert instance.is_connected()
    assert instance is shared_instance

    gateway_instance = await Account(testnet_gateway_account)
    user_instance = await Account(testnet_user_account)

    gateway_core_balance = await gateway_instance.balance(test_core_asset)
    user_core_balance = await user_instance.balance(test_core_asset)

    # If raise, add some TEST token to your testnet accounts. You can ask it in BitShares node admins or dev communities
    # 1 TEST token currently (2020) is enough for ~operations
    assert gateway_core_balance > 1
    assert user_core_balance > 1
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_issue_asset_nobroadcast():
    instance = await init_bitshares(account=testnet_gateway_account,
                                    node=testnet_bitshares_nodes,
                                    keys=[testnet_gateway_active, testnet_gateway_memo])
    user_instance = await Account(testnet_user_account)
    old_user_eth_balance = await user_instance.balance(test_eth_asset)

    _issue = await asset_issue(symbol=test_eth_asset, amount=TEST_ETH_AMOUNT, to=testnet_user_account)

    new_user_eth_balance = await user_instance.balance(test_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert (new_user_eth_balance.amount == old_user_eth_balance.amount)
    assert isinstance(_issue, dict)
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_issue_asset_broadcast():
    instance = await init_bitshares(account=testnet_gateway_account,
                                    node=testnet_bitshares_nodes,
                                    keys=[testnet_gateway_active, testnet_gateway_memo])
    user_instance = await Account(testnet_user_account)
    old_user_eth_balance = await user_instance.balance(test_eth_asset)

    _issue = await asset_issue(symbol=test_eth_asset, amount=TEST_ETH_AMOUNT, to=testnet_user_account)
    issue = await broadcast_tx(_issue)

    new_user_eth_balance = await user_instance.balance(test_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount

    assert (new_user_eth_balance.amount - old_user_eth_balance.amount) == TEST_ETH_AMOUNT
    assert isinstance(issue, dict)
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_burn_nobroadcast():
    instance = await init_bitshares(account=testnet_gateway_account,
                                    node=testnet_bitshares_nodes,
                                    keys=[testnet_gateway_active, testnet_gateway_memo])

    gateway_instance = await Account(testnet_gateway_account)
    old_gateway_eth_balance = await gateway_instance.balance(test_eth_asset)

    _burn = await asset_burn(symbol=test_eth_asset, amount=TEST_ETH_AMOUNT)
    new_gateway_eth_balance = await gateway_instance.balance(test_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert (new_gateway_eth_balance.amount == old_gateway_eth_balance.amount)
    assert isinstance(_burn, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_burn_broadcast():
    instance = await init_bitshares(account=testnet_gateway_account,
                                    node=testnet_bitshares_nodes,
                                    keys=[testnet_gateway_active, testnet_gateway_memo])

    gateway_instance = await Account(testnet_gateway_account)
    old_gateway_eth_balance = await gateway_instance.balance(test_eth_asset)

    _burn = await asset_burn(symbol=test_eth_asset, amount=TEST_ETH_AMOUNT)
    burn = await broadcast_tx(_burn)

    new_gateway_eth_balance = await gateway_instance.balance(test_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert (old_gateway_eth_balance.amount - new_gateway_eth_balance.amount) == TEST_ETH_AMOUNT
    assert isinstance(burn, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_transfer_nobroadcast():
    instance = await init_bitshares(account=testnet_gateway_account,
                                    node=testnet_bitshares_nodes,
                                    keys=[testnet_user_active, testnet_user_memo])

    user_instance = await Account(testnet_gateway_account)
    old_user_eth_balance = await user_instance.balance(test_eth_asset)

    _transfer = await asset_transfer(account=testnet_user_account,
                                     to=testnet_gateway_account,
                                     amount=TEST_ETH_AMOUNT,
                                     asset=test_eth_asset)
    new_user_eth_balance = await user_instance.balance(test_eth_asset)
    assert new_user_eth_balance.amount == old_user_eth_balance.amount
    assert isinstance(_transfer, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_transfer_broadcast():
    instance = await init_bitshares(account=testnet_gateway_account,
                                    node=testnet_bitshares_nodes,
                                    keys=[testnet_user_active, testnet_user_memo])
    gateway_instance = await Account(testnet_gateway_account)
    old_gateway_eth_balance = await gateway_instance.balance(test_eth_asset)

    _transfer = await asset_transfer(account=testnet_user_account,
                                     to=testnet_gateway_account,
                                     amount=TEST_ETH_AMOUNT,
                                     asset=test_eth_asset)
    transfer = await broadcast_tx(_transfer)

    new_gateway_eth_balance = await gateway_instance.balance(test_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert (new_gateway_eth_balance.amount - old_gateway_eth_balance.amount) == TEST_ETH_AMOUNT
    assert isinstance(transfer, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_await_new_account_ops():
    await init_bitshares(account=testnet_gateway_account,
                         node=testnet_bitshares_nodes,
                         keys=[testnet_user_active, testnet_user_memo])
    new_ops = await await_new_account_ops()
    assert isinstance(new_ops, list)
