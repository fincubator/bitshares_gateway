import pytest

from src.config import Config


def test_no_env_config():
    _cfg = Config()
    assert _cfg.db_port == 5432
