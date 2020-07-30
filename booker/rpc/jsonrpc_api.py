from typing import Any, Optional
from abc import abstractmethod
from uuid import UUID, uuid4
import logging

import marshmallow
from marshmallow.exceptions import (
    ValidationError as MarshmallowSchemaValidationError
)
from marshmallow_dataclass import dataclass

from booker.dto import DTOInvalidType, DataTransferClass
from booker.rpc.api import (
    APIMethodNotFound,
    APIUnknownOk,
    APIUnknownError,
    APIUnknownResult,
    APIsClient,
    APIsServer
)


class JSONRPCAPIResultAndError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class JSONRPCAPIParseError(Exception):
    def __init__(self, message: str, data: Optional[Any]) -> None:
        super().__init__(message, data)


class JSONRPCAPIInvalidRequest(Exception):
    def __init__(self, message: str, data: Optional[Any]) -> None:
        super().__init__(message, data)


class JSONRPCAPIMethodNotFound(Exception):
    def __init__(self, message: str, data: Optional[Any]) -> None:
        super().__init__(message, data)


class JSONRPCAPIInvalidParams(Exception):
    def __init__(self, message: str, data: Optional[Any]) -> None:
        super().__init__(message, data)


class JSONRPCAPIInternalError(Exception):
    def __init__(self, message: str, data: Optional[Any]) -> None:
        super().__init__(message, data)


class JSONRPCAPIServerError(Exception):
    def __init__(self, code: int, message: str, data: Optional[Any]) -> None:
        super().__init__(code, message, data)


@dataclass
class JSONRPCRequest(DataTransferClass):
    jsonrpc: str
    method: str
    id: UUID
    params: Optional[Any] = None


@dataclass
class JSONRPCRequestInternalParams(DataTransferClass):
    _coroutine_id: Optional[UUID] = None


@dataclass
class JSONRPCError(DataTransferClass):
    code: int
    message: str
    data: Optional[Any] = None


@dataclass
class JSONRPCResponse(DataTransferClass):
    jsonrpc: str
    result: Optional[Any]
    error: Optional[JSONRPCError]
    id: UUID


class JSONRPCAPIsClient(APIsClient):
    @abstractmethod
    async def _message_send_parent_transport_1(self, request: str) -> str:
        ...


    async def _message_send_parent_transport_0(
        self,
        method: str,
        coroutine_id: UUID,
        params: Optional[Any] = None
    ) -> Optional[Any]:
        try:
            if params is None:
                params = {}

            internal_params_schema = JSONRPCRequestInternalParams.Schema()
            request_schema = JSONRPCRequest.Schema()
            response_schema = JSONRPCResponse.Schema()
            internal_params = JSONRPCRequestInternalParams(
                _coroutine_id=coroutine_id
            )
            internal_params = internal_params_schema.dump(internal_params)

            params.update(internal_params)

            request = JSONRPCRequest(
                jsonrpc='2.0',
                method=method,
                id=uuid4(),
                params=params
            )

            logging.debug(f'client: request from client: {request}')

            request = request_schema.dumps(request)
            response = await self._message_send_parent_transport_1(request)
            response = response_schema.loads(response)

            logging.debug(f'client: response from server: {response}')

            if response.result is not None and response.error is not None:
                raise JSONRPCAPIResultAndError('Result and error are both set.')

            if response.error is not None:
                error = response.error

                if error.code == -32700:
                    raise JSONRPCAPIParseError(error.message, error.data)
                elif error.code == -32600:
                    raise JSONRPCAPIInvalidRequest(error.message, error.data)
                elif error.code == -32601:
                    raise JSONRPCAPIMethodNotFound(error.message, error.data)
                elif error.code == -32602:
                    raise JSONRPCAPIInvalidParams(error.message, error.data)
                elif error.code == -32603:
                    raise JSONRPCAPIInternalError(error.message, error.data)
                elif error.code >= -32099 and error.code <= -32000:
                    raise JSONRPCAPIServerError(
                        error.code,
                        error.message,
                        error.data
                    )

            return response.result
        except MarshmallowSchemaValidationError as exception:
            logging.debug(exception)

            raise DTOInvalidType(f'Invalid payload type: {exception}')


class JSONRPCAPIsServer(APIsServer):
    async def message_dispatch(self, request: str) -> str:
        try:
            request_schema = JSONRPCRequest.Schema()
            internal_params_schema = JSONRPCRequestInternalParams.Schema()
            response_schema = JSONRPCResponse.Schema()

            try:
                request = request_schema.loads(request)

                logging.debug(f'server: request from client: {request}')

                internal_params = internal_params_schema.load(
                    request.params,
                    unknown=marshmallow.EXCLUDE
                )
            except MarshmallowSchemaValidationError as exception:
                logging.debug(exception)

                response = JSONRPCResponse(
                    jsonrpc='2.0',
                    result=None,
                    error=JSONRPCError(
                        code=-32700,
                        message='Parse error',
                        data=exception.args
                    ),
                    id=request.id
                )

                logging.debug(f'server: response from server: {response}')

                response = response_schema.dumps(response)

                return response

            del request.params['_coroutine_id']

            if not request.params:
                request.params = None

            if internal_params._coroutine_id is None:
                internal_params._coroutine_id = uuid4()

            try:
                if request.params is None:
                    result = await super().message_dispatch(
                        request.method,
                        internal_params._coroutine_id
                    )
                else:
                    result = await super().message_dispatch(
                        request.method,
                        internal_params._coroutine_id,
                        request.params
                    )

                response = JSONRPCResponse(
                    jsonrpc='2.0',
                    result=result,
                    error=None,
                    id=request.id
                )
            except APIMethodNotFound as exception:
                logging.debug(exception)

                response = JSONRPCResponse(
                    jsonrpc='2.0',
                    result=None,
                    error=JSONRPCError(
                        code=-32601,
                        message='Method not found',
                        data=exception.args
                    ),
                    id=request.id
                )
            except (DTOInvalidType,
                    APIUnknownOk,
                    APIUnknownError,
                    APIUnknownResult) as exception:
                logging.debug(exception)

                response = JSONRPCResponse(
                    jsonrpc='2.0',
                    result=None,
                    error=JSONRPCError(
                        code=-32602,
                        message='Invalid params',
                        data=exception.args
                    ),
                    id=request.id
                )
            except BaseException as exception:
                logging.debug(exception)

                response = JSONRPCResponse(
                    jsonrpc='2.0',
                    result=None,
                    error=JSONRPCError(
                        code=-32603,
                        message='Internal error',
                        data=exception.args
                    ),
                    id=request.id
                )

            logging.debug(f'server: response from server: {response}')

            response = response_schema.dumps(response)

            return response

        except MarshmallowSchemaValidationError as exception:
            logging.debug(exception)

            raise DTOInvalidType(f'Invalid payload type: {exception}')
