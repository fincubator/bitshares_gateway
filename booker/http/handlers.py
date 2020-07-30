from aiohttp.web import (
    Request as HTTPRequest,
    Response as HTTPResponse,
    RouteTableDef as HTTPRouteTableDef,
)


handlers = HTTPRouteTableDef()


@handlers.get("/")
async def status(request: HTTPRequest) -> HTTPResponse:
    return HTTPResponse(text="Ok")
