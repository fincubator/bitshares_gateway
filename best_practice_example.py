import asyncio
import signal
import random
import weakref
from typing import Any, Iterator


class BlockChainEx(Exception):
    pass


class HTTPex(Exception):
    pass


class CriticalEx(Exception):
    pass


class DBConnector:
    """Example of EXTERNAL async object"""

    is_connected: bool

    def __init__(self):
        self.is_connected = True

    def __call__(self):
        return self.is_connected

    async def close(self):
        self.is_connected = False


async def blockchain_app():
    block = 0
    while True:
        if random.randint(1, 5) == 3:
            raise BlockChainEx
        print(f"Current block is {block}, database is ready: {ctx.database()()}")
        block += 1
        await asyncio.sleep(1)


async def http_app():
    uptime = 0
    while True:
        if random.randint(1, 5) == 3:
            raise HTTPex
        print(
            f"Server online dirung {uptime} seconds, database is ready: {ctx.database()()}"
        )
        uptime += 1
        await asyncio.sleep(1)


class AppContext:
    __slots__ = ("state", "DBConnector")
    state: dict

    def __init__(self):
        self.state = {}

    def __eq__(self, other: object) -> bool:
        return self is other

    def __getitem__(self, key: str) -> Any:
        return self.state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.state[key] = value

    def __delitem__(self, key: str) -> None:
        del self.state[key]

    def __len__(self) -> int:
        return len(self.state)

    def __iter__(self) -> Iterator[str]:
        return iter(self.state)

    def add(self, app):
        app_tmp = weakref.ref(app)
        self.state[app.__class__.__name__] = app_tmp

    @property
    def database(self):
        return self.state["DBConnector"]


def ex_handler(loop, ex_context):
    ex = ex_context.get("exception")
    message = ex_context["message"]
    print(f"Error: {ex.__class__.__name__}: {message}")

    if isinstance(ex, CriticalEx):
        print("Need to stop all")
        asyncio.create_task(shutdown(loop))

    else:
        coro_name = ex_context["future"].get_coro().__name__
        print(f"Continue work, create new instance of coroutine {coro_name}")
        if isinstance(ex, BlockChainEx) and coro_name == f"{blockchain_app.__name__}":
            asyncio.create_task(blockchain_app())

        elif isinstance(ex, HTTPex) and coro_name == f"{http_app.__name__}":
            asyncio.create_task(http_app())

        # More high-level exceptions processing...

        else:
            print(f"Catch unhandled exception, shutdown")
            asyncio.create_task(shutdown(loop))


async def shutdown(loop, signal=None):
    if signal:
        print(f"Received exit signal {signal.name}...")
    else:
        print("No exit signal")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    [task.cancel() for task in tasks]
    print(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)

    print(f"Make some post-shutdown things")
    loop.stop()


if __name__ == "__main__":

    # setup and configure loop
    loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s))
        )
    loop.set_exception_handler(ex_handler)

    #  Create context and add objects
    ctx = AppContext()
    db = DBConnector()

    ctx.add(db)

    # Execute
    try:
        loop.create_task(blockchain_app())
        loop.create_task(http_app())
        loop.run_forever()
    finally:
        loop.close()
        print("Successfully shutdown the app")
