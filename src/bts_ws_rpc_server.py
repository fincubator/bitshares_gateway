"""Some example of gateway's handlers.
You can change, add and remove handlers depending on gateway's architecture"""

import json

from booker.finteh_proto.server import BaseServer
from booker.finteh_proto.dto import (
    TransactionDTO,
    OrderDTO,
    DepositAddressDTO,
    ValidateAddressDTO,
)

from src.db_utils.queries import insert_operation, BitsharesOperation
from src.gw_dto import TxStatus, OrderType


class BtsWsRPCServer(BaseServer):
    def __init__(self, host="0.0.0.0", port=8080, ctx=None):
        super(BtsWsRPCServer, self).__init__(host, port, ctx)

        self.add_methods(
            ("", self.validate_address),
            ("", self.get_deposit_address),
            ("", self.init_new_tx),
        )

    async def init_new_tx(self, request):
        order = OrderDTO.Schema().load(request.msg[1]["params"])

        out_tx = order.out_tx
        out_tx.max_confirmations = self.ctx.cfg.max_confirmations
        out_tx.from_address = self.ctx.cfg.account

        async with self.ctx.db.acquire() as conn:
            insert = await insert_operation(
                conn,
                BitsharesOperation(
                    order_id=order.order_id,
                    order_type=OrderType.DEPOSIT,
                    asset=out_tx.coin,
                    from_account=out_tx.from_address,
                    to_account=out_tx.to_address,
                    amount=out_tx.amount,
                    status=TxStatus.WAIT,
                ),
            )

        return self.jsonrpc_response(request, out_tx)

    async def get_deposit_address(self, request):
        # Do not forget to overwrite this method to implement returning real deposit address
        deposit_address_body = DepositAddressDTO.Schema().load(request.msg[1]["params"])
        assert deposit_address_body.user
        deposit_address_body.deposit_address = self.ctx.cfg.account
        return self.jsonrpc_response(request, deposit_address_body)

    async def validate_address(self, request):
        # Do not forget to overwrite this method to implement gateway side blockchain address validation
        validate_address_body = ValidateAddressDTO.Schema().load(
            request.msg[1]["params"]
        )

        assert validate_address_body.user
        validate_address_body.is_valid = True

        return self.jsonrpc_response(request, validate_address_body)
