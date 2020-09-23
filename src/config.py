from os import getenv
from pathlib import Path

from dotenv import load_dotenv
import yaml

from src.utils import get_logger

log = get_logger("Config build")

project_root_dir = Path(__file__).parent.parent

BITSHARES_BLOCK_TIME = 3
BITSHARES_NEED_CONF = 5


class Config:
    is_test_env: bool = True

    db_driver: str = "postgres+psycopg2"
    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_database: str = "postgres"

    http_host: str = "0.0.0.0"
    http_port: int = 9999

    control_center_url: str = ""

    booker_host: str = "0.0.0.0"
    booker_port: int = 8888

    core_asset: str = "TEST"
    gateway_prefix: str = "FINTEHTEST"
    gateway_distribute_asset: str = "ETH"
    account: str = "fincubator-gateway-test"
    keys: dict = {
        "active": "5JEEBPVnDwttRkbLzmFKmgoZ1ELxBMnjnEiX4JhvVfeDNQbX936",
        "memo": "5KfyHL8gzAKiKz3wcc3c4EJgQi64nkuYZqAUN63QD5xxa2FogdW",
    }
    nodes: list or str = ["wss://testnet.dex.trading/"]

    min_deposit: float = 0.1
    min_withdrawal: float = 0.1
    max_deposit: float = 0.1
    max_withdrawal: float = 0.1

    def with_environment(self) -> None:
        try:
            """Using two files:
            `.env` file as server configurations (hosts, ports, etc. for local services)
            `gateway.yml` file as client configurations (remote addresses, account etc.)
            """

            try:
                load_dotenv()
                _env_params = {
                    "db_driver": getenv("DATABASE_DRIVER"),
                    "db_host": getenv("DATABASE_HOST"),
                    "db_port": getenv("DATABASE_PORT"),
                    "db_user": getenv("DATABASE_USERNAME"),
                    "db_password": getenv("DATABASE_PASSWORD"),
                    "db_database": getenv("DATABASE_NAME"),
                    "http_host": getenv("HTTP_HOST"),
                    "http_port": getenv("HTTP_PORT"),
                    "booker_host": getenv("BOOKER_HOST"),
                    "booker_port": getenv("BOOKER_PORT"),
                }
                for name, value in _env_params.items():
                    if not value:
                        log.info(f"bad value for {name}: {value}")
                        raise AttributeError
                    setattr(self, name, value)
                log.info("Successfully loaded user's .env configuration")

            except Exception as ex:
                log.info(
                    f"Unable to load config from .env file: {ex}. Using default values"
                )
                _env_params = {}

            try:
                from_gateway_yml = yaml.safe_load(
                    open(f"{project_root_dir}/gateway.yml", "r")
                )
                _gateway_yml_params = {
                    "core_asset": from_gateway_yml["core_asset"],
                    "gateway_prefix": from_gateway_yml["gateway_prefix"],
                    "gateway_distribute_asset": from_gateway_yml[
                        "gateway_distribute_asset"
                    ],
                    "account": from_gateway_yml["account"],
                    "nodes": from_gateway_yml["nodes"],
                    "min_deposit": from_gateway_yml["min_deposit"],
                    "min_withdrawal": from_gateway_yml["min_withdrawal"],
                    "max_deposit": from_gateway_yml["max_deposit"],
                    "max_withdrawal": from_gateway_yml["max_withdrawal"],
                }
                for name, value in _gateway_yml_params.items():
                    if not value:
                        log.info(f"bad value for {name}: {value}")
                        raise AttributeError

                    setattr(self, name, value)
                log.info("Successfully loaded user's gateway.yml configuration")

            except Exception as ex:
                log.info(
                    f"Unable to load config from gateway.yml file: {ex}. Using default values"
                )
                _gateway_yml_params = {}

            if _env_params and _gateway_yml_params:
                self.is_test_env = False

        except Exception as ex:
            log.info(f"Unable to build config: {ex}. Use default values")
