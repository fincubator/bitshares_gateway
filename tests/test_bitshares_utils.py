import pytest

from src.blockchain.bitshares_utils import *
from src.config import Config
from .fixtures import *


cfg = Config()


@pytest.mark.asyncio
async def test_init_bitshares():
    instance = await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)
    shared_instance = shared_bitshares_instance()

    assert instance.is_connected()
    assert instance is shared_instance

    gateway_instance = await Account(cfg.account)
    user_instance = await Account(testnet_user_account)

    gateway_core_balance = await gateway_instance.balance(cfg.core_asset)
    user_core_balance = await user_instance.balance(cfg.core_asset)

    # If raise, add some TEST token to your testnet accounts. You can ask some in BitShares node admin/dev communities
    # 1 TEST token currently (2020) is enough for ~operations
    assert gateway_core_balance > 1
    assert user_core_balance > 1
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_issue_asset_nobroadcast():
    instance = await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)
    user_instance = await Account(testnet_user_account)
    old_user_eth_balance = await user_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    _issue = await asset_issue(
        symbol=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        amount=TEST_ETH_AMOUNT,
        to=testnet_user_account,
    )

    new_user_eth_balance = await user_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert new_user_eth_balance.amount == old_user_eth_balance.amount
    assert isinstance(_issue, dict)
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_issue_asset_broadcast():
    instance = await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)
    user_instance = await Account(testnet_user_account)
    old_user_eth_balance = await user_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    _issue = await asset_issue(
        symbol=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        amount=TEST_ETH_AMOUNT,
        to=testnet_user_account,
    )
    issue = await broadcast_tx(_issue)

    new_user_eth_balance = await user_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount

    assert (
        new_user_eth_balance.amount - old_user_eth_balance.amount
    ) == TEST_ETH_AMOUNT
    assert isinstance(issue, dict)
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_burn_nobroadcast():
    instance = await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)

    gateway_instance = await Account(cfg.account)
    old_gateway_eth_balance = await gateway_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    _burn = await asset_burn(
        symbol=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        amount=TEST_ETH_AMOUNT,
    )
    new_gateway_eth_balance = await gateway_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert new_gateway_eth_balance.amount == old_gateway_eth_balance.amount
    assert isinstance(_burn, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_burn_broadcast():
    instance = await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)

    gateway_instance = await Account(cfg.account)
    old_gateway_eth_balance = await gateway_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    _burn = await asset_burn(
        symbol=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        amount=TEST_ETH_AMOUNT,
    )
    burn = await broadcast_tx(_burn)

    new_gateway_eth_balance = await gateway_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert (
        old_gateway_eth_balance.amount - new_gateway_eth_balance.amount
    ) == TEST_ETH_AMOUNT
    assert isinstance(burn, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_read_memo():
    instance = await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)

    assert (await read_memo(testnet_memo_dict)) == testnet_memo_string

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_transfer_nobroadcast():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )

    user_instance = await Account(cfg.account)
    old_user_eth_balance = await user_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    _transfer = await asset_transfer(
        account=testnet_user_account,
        to=cfg.account,
        amount=TEST_ETH_AMOUNT,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
    )
    new_user_eth_balance = await user_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )
    assert new_user_eth_balance.amount == old_user_eth_balance.amount
    assert isinstance(_transfer, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_transfer_broadcast():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    gateway_instance = await Account(cfg.account)
    old_gateway_eth_balance = await gateway_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    _transfer = await asset_transfer(
        account=testnet_user_account,
        to=cfg.account,
        amount=TEST_ETH_AMOUNT,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        memo=testnet_memo_string,
    )
    transfer = await broadcast_tx(_transfer)

    new_gateway_eth_balance = await gateway_instance.balance(
        f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}"
    )

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert (
        new_gateway_eth_balance.amount - old_gateway_eth_balance.amount
    ) == TEST_ETH_AMOUNT
    assert isinstance(transfer, dict)
    assert (
        await read_memo(transfer["operations"][0][1]["memo"])
    ) == testnet_memo_string
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_await_new_account_ops():
    instance = await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)
    new_ops = await wait_new_account_ops()
    assert isinstance(new_ops, list)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_get_last_op_num():
    await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)
    last_op = await get_last_op_num(cfg.account)
    assert isinstance(last_op, int)


@pytest.mark.asyncio
async def test_withdrawal_validate_success():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=cfg.account,
        amount=0.1,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        memo="eTh:123456",
    )

    withdrawal = await broadcast_tx(_withdrawal)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)

    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            broadcasted_id = Signed_Transaction(withdrawal).id
            in_block_id = Signed_Transaction(tx).id
            if broadcasted_id == in_block_id:
                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.order_type == OrderType.WITHDRAWAL
                assert not validated.error != TxError.NO_ERROR

    assert txid_match


@pytest.mark.asyncio
async def test_withdrawal_validate_bad_amount_less_min():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=cfg.account,
        amount=test_min_withdrawal * 0.99,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        memo="eTh:123456",
    )

    withdrawal = await broadcast_tx(_withdrawal)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)

    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            if Signed_Transaction(withdrawal).id == Signed_Transaction(tx).id:
                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.error == TxError.LESS_MIN
                assert validated.status == TxStatus.ERROR

    assert txid_match


@pytest.mark.asyncio
async def test_withdrawal_validate_bad_amount_greater_max():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=cfg.account,
        amount=test_max_withdrawal * 1.1,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        memo="eTh:123456",
    )

    withdrawal = await broadcast_tx(_withdrawal)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)

    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            if Signed_Transaction(withdrawal).id == Signed_Transaction(tx).id:
                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.error == TxError.GREATER_MAX
                assert validated.status == TxStatus.ERROR

    assert txid_match


@pytest.mark.asyncio
async def test_withdrawal_validate_bad_asset():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=cfg.account,
        amount=0.1,
        asset=testnet_usdt_asset,
        memo="eTh:123456",
    )

    withdrawal = await broadcast_tx(_withdrawal)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)

    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            if Signed_Transaction(withdrawal).id == Signed_Transaction(tx).id:
                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.error == TxError.BAD_ASSET
                assert validated.status == TxStatus.ERROR

    assert txid_match


@pytest.mark.asyncio
async def test_withdrawal_validate_memo_no_memo():

    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=cfg.account,
        amount=0.1,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
    )

    withdrawal = await broadcast_tx(_withdrawal)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)
    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            if Signed_Transaction(withdrawal).id == Signed_Transaction(tx).id:
                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.error == TxError.NO_MEMO
                assert validated.status == TxStatus.ERROR

    assert txid_match


@pytest.mark.asyncio
async def test_withdrawal_validate_flood_memo():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=cfg.account,
        amount=0.1,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        memo=":",
    )

    withdrawal = await broadcast_tx(_withdrawal)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)
    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            if Signed_Transaction(withdrawal).id == Signed_Transaction(tx).id:
                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.error == TxError.FLOOD_MEMO
                assert validated.status == TxStatus.ERROR

    assert txid_match


@pytest.mark.asyncio
async def test_deposit_validate_success():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _deposit = await asset_transfer(
        account=cfg.account,
        to=testnet_user_account,
        amount=0.1,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        memo="flood",
    )

    deposit = await broadcast_tx(_deposit)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)

    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            if Signed_Transaction(deposit).id == Signed_Transaction(tx).id:
                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.order_type == OrderType.DEPOSIT
                assert validated.error == TxError.NO_ERROR

    assert txid_match


@pytest.mark.asyncio
async def test_deposit_validate_less_min():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _deposit = await asset_transfer(
        account=cfg.account,
        to=testnet_user_account,
        amount=test_min_deposit * 0.99,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        memo="flood",
    )

    deposit = await broadcast_tx(_deposit)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)

    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            if Signed_Transaction(deposit).id == Signed_Transaction(tx).id:
                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.order_type == OrderType.DEPOSIT
                assert validated.status == TxStatus.ERROR
                assert validated.error == TxError.LESS_MIN

    assert txid_match


@pytest.mark.asyncio
async def test_deposit_validate_greater_max():
    instance = await init_bitshares(
        account=cfg.account,
        node=cfg.nodes,
        keys=[
            cfg.keys["active"],
            cfg.keys["memo"],
            testnet_user_memo,
            testnet_user_active,
        ],
    )
    previous_last_op_num = await get_last_op_num(cfg.account)

    _deposit = await asset_transfer(
        account=cfg.account,
        to=testnet_user_account,
        amount=test_max_deposit * 1.11,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
    )

    deposit = await broadcast_tx(_deposit)
    new_ops = await wait_new_account_ops(last_op=previous_last_op_num)

    txid_match = False
    for op in new_ops:
        op_block: Block = await Block(op["block_num"])
        for tx in op_block["transactions"]:
            if Signed_Transaction(deposit).id == Signed_Transaction(tx).id:

                txid_match = True
                assert len(tx["operations"]) == 1
                validated = await validate_op(op)
                assert validated.order_type == OrderType.DEPOSIT
                assert validated.status == TxStatus.ERROR
                assert validated.error == TxError.GREATER_MAX

    assert txid_match


@pytest.mark.asyncio
async def test_confirm_old_op():
    await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)

    op_dto = BitSharesOperationDTO(
        op_id=43571314,
        order_type=OrderType.DEPOSIT,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        from_account=cfg.account,
        to_account=testnet_user_account,
        amount=0.1,
        status=TxStatus.RECEIVED_NOT_CONFIRMED,
        confirmations=0,
        block_num=37899972,
        tx_created_at=(await Block(37899972)).time(),
        error=TxError.NO_ERROR,
    )

    await confirm_op(op_dto)
    assert op_dto.status == TxStatus.RECEIVED_AND_CONFIRMED
    assert op_dto.confirmations > 0


@pytest.mark.asyncio
async def test_get_tx_hash_from_op_success():
    await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)

    account = await Account(cfg.account)
    history_agen = account.history()
    op = [op async for op in history_agen][0]
    tx_hash = await get_tx_hash_from_op(op)

    assert tx_hash
    assert isinstance(tx_hash, str)


@pytest.mark.asyncio
async def test_validate_bitshares_account():
    await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)

    assert await validate_bitshares_account("kwaskoff")
    assert not await validate_bitshares_account("1kwaskoff")
