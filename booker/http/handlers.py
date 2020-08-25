from functools import partial
from uuid import UUID
from src.utils import get_logger

from aiohttp.web import (
    Request as HTTPRequest,
    Response as HTTPResponse,
    RouteTableDef as HTTPRouteTableDef,
    json_response as http_json_response,
)

from booker.app import AppContext
from booker.frontend.dto import NewInOrder, InOrder, Order
from booker.frontend import api


log = get_logger("BookerApp")


async def status(context: AppContext, request: HTTPRequest) -> HTTPResponse:
    return HTTPResponse(text="Ok")


async def new_in_order(context: AppContext, request: HTTPRequest) -> HTTPResponse:
    rq_payload = await request.json()
    new_order_shema = NewInOrder.Schema()
    new_order = new_order_shema.load(rq_payload)
    order = await api.new_in_order(context, new_order)
    order_shema = InOrder.Schema()
    rs_payload = order_shema.dump(order)
    response = http_json_response(rs_payload)

    return response


async def get_order(context: AppContext, request: HTTPRequest) -> HTTPResponse:
    order_id = UUID(request.match_info["order_id"])
    order = await api.get_order(context, order_id)
    order_shema = Order.Schema()
    rs_payload = order_shema.dump(order)
    response = http_json_response(rs_payload)

    return response


def construct_handlers(context: AppContext, handlers: HTTPRouteTableDef) -> None:
    handlers.get("/")(partial(status, context))
    handlers.post("/orders")(partial(new_in_order, context))
    handlers.get("/orders/{order_id}")(partial(get_order, context))
