import weakref
from getpass import getpass
from typing import Any, Iterator

from src.config import Config


class AppContext:
    __slots__ = ("state", "Engine", "BitShares", "cfg")
    state: dict

    def __init__(self):
        self.state = {}
        self.cfg = Config()

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
    def db(self):
        return self.state["Engine"]


ctx = AppContext()
print(ctx.cfg)
