from typing import (
    TypeVar,
    Callable,
    Any,
    Optional,
    AsyncGenerator,
    Type,
    get_type_hints,
    get_args as get_type_args,
    Mapping,
)
from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from builtins import *
from src.utils import get_logger

from marshmallow.exceptions import ValidationError as MarshmallowSchemaValidationError
from marshmallow_dataclass import dataclass

from booker.dto import DTOInvalidType, DataTransferClass


log = get_logger("BookerRPCAPI")


RAPIStream = TypeVar("RAPIStream")


SAPIStream = TypeVar("SAPIStream")


APIStream = AsyncGenerator[Optional[RAPIStream], Optional[SAPIStream]]


APIMethod = Callable[[Any, Optional[Any]], APIStream]


class APIAlreadyRegistered(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class APIMethodNotFound(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class APIUnknownOk(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class APIUnknownError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class APIUnknownResult(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class APIOk(DataTransferClass):
    name: str
    ok: Any


@dataclass
class APIError(DataTransferClass):
    name: str
    error: Any


@dataclass
class APIResult(DataTransferClass):
    name: str
    ok_or_error: Any


class APIsClient(ABC):
    @abstractmethod
    async def _message_send_parent_transport_0(
        self, method: str, coroutine_id: UUID, args: Optional[Any] = None
    ) -> Optional[Any]:
        ...

    async def message_send(
        self,
        class_name: str,
        method_name: str,
        coroutine_id: UUID,
        args: Optional[Any] = None,
    ) -> Optional[Any]:
        path = ".".join([class_name, method_name])
        result = await self._message_send_parent_transport_0(path, coroutine_id, args)

        return result


class APIClient(ABC):
    apis_client: APIsClient

    def __init__(self, apis_client: APIsClient) -> None:
        super().__init__()

        self.apis_client = apis_client

    async def message_dispatch(
        self, method_name: str, type_hints: Any, typed_args: Optional[Any] = None
    ) -> APIStream[Any, Any]:
        try:
            class_name = type(self).__name__[:-6]
            args_schema = type_hints["args"].Schema()
            args = args_schema.dump(typed_args)
            ok_schema = APIOk.Schema()
            error_schema = APIError.Schema()
            result_schema = APIResult.Schema()
            async_generator_type = type_hints["return"]
            async_generator_type_args = get_type_args(async_generator_type)
            send_types = async_generator_type_args[1]
            send_types_args = get_type_args(send_types)
            send_schemas = {
                schema.__name__: schema.Schema()
                for schema in send_types_args
                if schema is not type(None)
            }
            result_types = async_generator_type_args[0]
            result_types_args = get_type_args(result_types)
            result_schemas = {
                schema.__name__: schema.Schema()
                for schema in result_types_args
                if schema is not type(None)
            }
            coroutine_id = uuid4()
            send = args

            while True:
                result = await self.apis_client.message_send(
                    class_name, method_name, coroutine_id, send
                )
                ok_result = None

                if result is not None:
                    result = result_schema.load(result)

                    if result.name == "ok":
                        ok_result = ok_schema.load(result.ok_or_error)

                        if ok_result.name not in result_schemas:
                            raise APIUnknownOk(f"Unknown schema: {ok_result.name}")

                        ok_result_schema = result_schemas[ok_result.name]
                        ok_result = ok_result_schema.load(ok_result.ok)
                    elif result.name == "error":
                        error_result = error_schema.load(result.ok_or_error)

                        if error_result.name == "StopAsyncIteration":
                            return

                        if error_result.name not in globals():
                            raise APIUnknownError(
                                f"Unknown schema: {error_result.name}"
                            )

                        exception_class = globals()[error_result.name]
                        exception = exception_class(*error_result.error)

                        raise exception
                    else:
                        raise APIUnknownResult(f"Unknown schema: {result.name}")

                try:
                    ok_send = yield ok_result
                except BaseException as exception:
                    log.debug(exception)

                    error_send_name = type(exception).__name__
                    error_send = APIError(name=error_send_name, error=exception.args)
                    error_send = error_schema.dump(error_send)
                    send = APIResult(name="error", ok_or_error=error_send)
                    send = result_schema.dump(send)

                    continue

                if ok_send is None:
                    send = None

                    continue

                ok_send_name = type(ok_send).__name__

                if ok_send_name not in send_schemas:
                    raise APIUnknownOk(f"Unknown schema: {ok_send_name}")

                ok_send_schema = send_schemas[ok_send_name]
                ok_send = ok_send_schema.dump(ok_send)
                ok_send = APIOk(name=ok_send_name, ok=ok_send)
                ok_send = ok_schema.dump(ok_send)
                send = APIResult(name="ok", ok_or_error=ok_send)
                send = result_schema.dump(send)
        except MarshmallowSchemaValidationError as exception:
            log.debug(exception)

            raise DTOInvalidType(f"Invalid payload type: {exception}")


class APIServer(ABC):
    @abstractmethod
    async def message_dispatch(
        self, method_name: str, args: Optional[Any] = None
    ) -> APIStream[Any, Any]:
        raise APIMethodNotFound(f"Method {method_name} not found.")
        # Typing hack
        yield


class APIsServer:
    apis: Mapping[str, APIServer]
    coroutines: Mapping[UUID, APIStream]

    def __init__(self) -> None:
        super().__init__()

        self.apis = {}
        self.coroutines = {}

    def api_register(self, api: APIServer) -> None:
        api_name = type(api).__name__[:-6]

        if api_name in self.apis:
            raise APIAlreadyRegistered(
                f"API is already registered: name {api_name} is already " "occupied"
            )
        else:
            self.apis[api_name] = api

    async def message_dispatch(
        self, path: str, coroutine_id: UUID, args: Optional[Any] = None
    ) -> Optional[Any]:
        splitted_path = str.rsplit(path, ".", 1)
        class_name = splitted_path[0]
        method_name = splitted_path[1]
        api = self.apis[class_name]
        init = False

        if coroutine_id in self.coroutines:
            coroutine = self.coroutines[coroutine_id]
        else:
            init = True
            coroutine = api.message_dispatch(method_name, args)
            self.coroutines[coroutine_id] = coroutine

        if init:
            result = await coroutine.asend(None)
        else:
            result = await coroutine.asend(args)

        return result


def api_method(method: APIMethod) -> APIMethod:
    method.is_api_method = True

    return method


def api_client(api_def: Type[ABC]) -> Type[ABC]:
    class APIClientDef(api_def, APIClient):
        ...

    for method_name in APIClientDef.__abstractmethods__:
        method = getattr(APIClientDef, method_name)
        is_api_method = getattr(method, "is_api_method", False)

        if is_api_method:
            type_hints = get_type_hints(method)

            setattr(
                APIClientDef,
                method_name,
                lambda api_client, args, method_name=method_name, type_hints=type_hints: api_client.message_dispatch(
                    method_name, type_hints, args
                ),
            )

    return APIClientDef


def api_server(api_def: Type[object]) -> Type[object]:
    class APIServerDef(api_def, APIServer):
        async def message_dispatch(
            self, method_name: str, args: Optional[Any] = None
        ) -> APIStream[Any, Any]:
            try:
                method = getattr(type(self), method_name, None)
                is_api_method = getattr(method, "is_api_method", False)

                if method is None or not is_api_method:
                    ok_send = None
                    error_send = None
                    send_exception = False
                    coroutine = super().message_dispatch(method_name, args)

                    while True:
                        try:
                            if send_exception:
                                ok_result = await coroutine.athrow(error_send)
                            else:
                                ok_result = await coroutine.asend(ok_send)
                        except APIMethodNotFound as exception:
                            log.debug(exception)

                            raise exception
                        except BaseException as exception:
                            log.debug(exception)

                            error_result_name = type(exception).__name__
                            error_result = APIError(
                                name=error_result_name, error=exception.args
                            )
                            error_result = error_schema.dump(error_result)
                            result = APIResult(name="error", ok_or_error=error_result)
                            result = result_schema.dump(result)

                            yield result
                            return

                        result = None

                        if ok_result is not None:
                            result = APIResult(name="ok", ok_or_error=ok_result)
                            result = result_schema.dump(result)

                        send = yield result

                        ok_send = None
                        error_send = None

                        if send is None:
                            continue

                        send = result_schema.load(send)

                        if send.name == "ok":
                            ok_send = ok_schema.load(send.ok_or_error)
                            ok_send = ok_send.ok
                            send_exception = False
                        elif send.name == "error":
                            error_send = error_schema.load(send.ok_or_error)

                            if error_send.name not in globals():
                                raise APIUnknownError(
                                    f"Unknown schema: {error_send.name}"
                                )

                            exception_class = globals()[error_send.name]
                            error_send = exception_class(*error_send.error)
                            send_exception = True

                type_hints = get_type_hints(method)
                args_schema = type_hints["args"].Schema()
                typed_args = args_schema.load(args)
                ok_schema = APIOk.Schema()
                error_schema = APIError.Schema()
                result_schema = APIResult.Schema()
                async_generator_type = type_hints["return"]
                async_generator_type_args = get_type_args(async_generator_type)
                send_types = async_generator_type_args[1]
                send_types_args = get_type_args(send_types)
                send_schemas = {
                    schema.__name__: schema.Schema()
                    for schema in send_types_args
                    if schema is not type(None)
                }
                result_types = async_generator_type_args[0]
                result_types_args = get_type_args(result_types)
                result_schemas = {
                    schema.__name__: schema.Schema()
                    for schema in result_types_args
                    if schema is not type(None)
                }
                coroutine = method(self, typed_args)
                ok_send = None
                error_send = None
                send_exception = False

                while True:
                    try:
                        if send_exception:
                            ok_result = await coroutine.athrow(error_send)
                        else:
                            ok_result = await coroutine.asend(ok_send)
                    except BaseException as exception:
                        log.debug(exception)

                        error_result_name = type(exception).__name__
                        error_result = APIError(
                            name=error_result_name, error=exception.args
                        )
                        error_result = error_schema.dump(error_result)
                        result = APIResult(name="error", ok_or_error=error_result)
                        result = result_schema.dump(result)

                        yield result
                        return

                    result = None

                    if ok_result is not None:
                        ok_result_name = type(ok_result).__name__

                        if ok_result_name not in result_schemas:
                            raise APIUnknownOk(f"Unknown schema: {ok_result_name}")

                        ok_result_schema = result_schemas[ok_result_name]
                        ok_result = ok_result_schema.dump(ok_result)
                        ok_result = APIOk(name=ok_result_name, ok=ok_result)
                        ok_result = ok_schema.dump(ok_result)
                        result = APIResult(name="ok", ok_or_error=ok_result)
                        result = result_schema.dump(result)

                    send = yield result
                    ok_send = None
                    error_send = None

                    if send is None:
                        continue

                    send = result_schema.load(send)

                    if send.name == "ok":
                        ok_send = ok_schema.load(send.ok_or_error)

                        if ok_send.name not in send_schemas:
                            raise APIUnknownOk(f"Unknown schema: {ok_send.name}")

                        ok_send_schema = send_schemas[ok_send.name]
                        ok_send = ok_send_schema.load(ok_send.ok)
                        send_exception = False
                    elif send.name == "error":
                        error_send = error_schema.load(send.ok_or_error)

                        if error_send.name not in globals():
                            raise APIUnknownError(f"Unknown schema: {error_send.name}")

                        exception_class = globals()[error_send.name]
                        error_send = exception_class(*error_send.error)
                        send_exception = True
            except MarshmallowSchemaValidationError as exception:
                log.debug(exception)

                raise DTOInvalidType(f"Invalid payload type: {exception}")

    return APIServerDef
