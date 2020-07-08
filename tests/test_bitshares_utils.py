import pytest

from src.bitshares_utils import *

from .fixtures import *


@pytest.mark.asyncio
async def test_init_bitshares():
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_gateway_active, testnet_gateway_memo],
    )
    shared_instance = shared_bitshares_instance()

    assert instance.is_connected()
    assert instance is shared_instance

    gateway_instance = await Account(testnet_gateway_account)
    user_instance = await Account(testnet_user_account)

    gateway_core_balance = await gateway_instance.balance(testnet_core_asset)
    user_core_balance = await user_instance.balance(testnet_core_asset)

    # If raise, add some TEST token to your testnet accounts. You can ask it in BitShares node admins or dev communities
    # 1 TEST token currently (2020) is enough for ~operations
    assert gateway_core_balance > 1
    assert user_core_balance > 1
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_issue_asset_nobroadcast():
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_gateway_active, testnet_gateway_memo],
    )
    user_instance = await Account(testnet_user_account)
    old_user_eth_balance = await user_instance.balance(testnet_eth_asset)

    _issue = await asset_issue(
        symbol=testnet_eth_asset, amount=TEST_ETH_AMOUNT, to=testnet_user_account
    )

    new_user_eth_balance = await user_instance.balance(testnet_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert new_user_eth_balance.amount == old_user_eth_balance.amount
    assert isinstance(_issue, dict)
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_issue_asset_broadcast():
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_gateway_active, testnet_gateway_memo],
    )
    user_instance = await Account(testnet_user_account)
    old_user_eth_balance = await user_instance.balance(testnet_eth_asset)

    _issue = await asset_issue(
        symbol=testnet_eth_asset, amount=TEST_ETH_AMOUNT, to=testnet_user_account
    )
    issue = await broadcast_tx(_issue)

    new_user_eth_balance = await user_instance.balance(testnet_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount

    assert (
        new_user_eth_balance.amount - old_user_eth_balance.amount
    ) == TEST_ETH_AMOUNT
    assert isinstance(issue, dict)
    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_burn_nobroadcast():
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_gateway_active, testnet_gateway_memo],
    )

    gateway_instance = await Account(testnet_gateway_account)
    old_gateway_eth_balance = await gateway_instance.balance(testnet_eth_asset)

    _burn = await asset_burn(symbol=testnet_eth_asset, amount=TEST_ETH_AMOUNT)
    new_gateway_eth_balance = await gateway_instance.balance(testnet_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert new_gateway_eth_balance.amount == old_gateway_eth_balance.amount
    assert isinstance(_burn, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_burn_broadcast():
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_gateway_active, testnet_gateway_memo],
    )

    gateway_instance = await Account(testnet_gateway_account)
    old_gateway_eth_balance = await gateway_instance.balance(testnet_eth_asset)

    _burn = await asset_burn(symbol=testnet_eth_asset, amount=TEST_ETH_AMOUNT)
    burn = await broadcast_tx(_burn)

    new_gateway_eth_balance = await gateway_instance.balance(testnet_eth_asset)

    # .amount cause asyncio bitshares currently dont support some math operations
    # When it will be implemented, need to remove .amount
    assert (
        old_gateway_eth_balance.amount - new_gateway_eth_balance.amount
    ) == TEST_ETH_AMOUNT
    assert isinstance(burn, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_read_memo():
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_user_active, testnet_user_memo],
    )

    assert (await read_memo(testnet_memo_dict)) == testnet_memo_string

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_transfer_nobroadcast():
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_user_active, testnet_user_memo],
    )

    user_instance = await Account(testnet_gateway_account)
    old_user_eth_balance = await user_instance.balance(testnet_eth_asset)

    _transfer = await asset_transfer(
        account=testnet_user_account,
        to=testnet_gateway_account,
        amount=TEST_ETH_AMOUNT,
        asset=testnet_eth_asset,
    )
    new_user_eth_balance = await user_instance.balance(testnet_eth_asset)
    assert new_user_eth_balance.amount == old_user_eth_balance.amount
    assert isinstance(_transfer, dict)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_asset_transfer_broadcast():
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_user_active, testnet_user_memo],
    )
    gateway_instance = await Account(testnet_gateway_account)
    old_gateway_eth_balance = await gateway_instance.balance(testnet_eth_asset)

    _transfer = await asset_transfer(
        account=testnet_user_account,
        to=testnet_gateway_account,
        amount=TEST_ETH_AMOUNT,
        asset=testnet_eth_asset,
        memo=testnet_memo_string,
    )
    transfer = await broadcast_tx(_transfer)

    new_gateway_eth_balance = await gateway_instance.balance(testnet_eth_asset)

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
    instance = await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_user_active, testnet_user_memo],
    )
    new_ops = await wait_new_account_ops()
    assert isinstance(new_ops, list)

    await instance.rpc.connection.disconnect()


@pytest.mark.asyncio
async def test_get_last_op_num():
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[testnet_user_active, testnet_user_memo],
    )
    last_op = await get_last_op_num(testnet_gateway_account)
    assert isinstance(last_op, int)


@pytest.mark.asyncio
async def test_withdrawal_validate_success():
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )
    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=testnet_gateway_account,
        amount=0.1,
        asset=testnet_eth_asset,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=testnet_gateway_account,
        amount=test_gateway_min_withdrawal * 0.99,
        asset=testnet_eth_asset,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=testnet_gateway_account,
        amount=test_gateway_max_withdrawal * 1.1,
        asset=testnet_eth_asset,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=testnet_gateway_account,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=testnet_gateway_account,
        amount=0.1,
        asset=testnet_eth_asset,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _withdrawal = await asset_transfer(
        account=testnet_user_account,
        to=testnet_gateway_account,
        amount=0.1,
        asset=testnet_eth_asset,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _deposit = await asset_transfer(
        account=testnet_gateway_account,
        to=testnet_user_account,
        amount=0.1,
        asset=testnet_eth_asset,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _deposit = await asset_transfer(
        account=testnet_gateway_account,
        to=testnet_user_account,
        amount=test_gateway_min_deposit * 0.99,
        asset=testnet_eth_asset,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    previous_last_op_num = await get_last_op_num(testnet_gateway_account)

    _deposit = await asset_transfer(
        account=testnet_gateway_account,
        to=testnet_user_account,
        amount=test_gateway_max_deposit * 1.11,
        asset=testnet_eth_asset,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    op_dto = BitSharesOperationDTO(
        op_id=43571314,
        order_type=OrderType.DEPOSIT,
        asset=testnet_eth_asset,
        from_account=testnet_gateway_account,
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
    await init_bitshares(
        account=testnet_gateway_account,
        node=testnet_bitshares_nodes,
        keys=[
            testnet_user_active,
            testnet_user_memo,
            testnet_gateway_active,
            testnet_gateway_memo,
        ],
    )

    account = await Account(testnet_gateway_account)
    history_agen = account.history()
    op = [op async for op in history_agen][0]
    tx_hash = await get_tx_hash_from_op(op)

    assert tx_hash
    assert isinstance(tx_hash, str)
