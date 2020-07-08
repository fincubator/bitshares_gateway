from pathlib import Path
import os

import yaml
from dotenv import load_dotenv

from config.const import *


load_dotenv()

project_root_dir = Path(__file__).parent.parent

try:
    gateway_cfg = yaml.safe_load(open(f"{project_root_dir}/config/gateway.yml", "r"))

except FileNotFoundError:
    print("Use testnet config from fixtures!")
    # If config/gateway.yml is not provided, using testnet fixtures"
    from tests.fixtures import (
        testnet_gateway_account,
        testnet_gateway_memo,
        testnet_gateway_active,
        testnet_gateway_prefix,
        testnet_core_asset,
        testnet_bitshares_nodes,
        testnet_eth_asset,
        test_gateway_min_deposit,
        test_gateway_max_deposit,
        test_gateway_max_withdrawal,
        test_gateway_min_withdrawal,
    )

    gateway_cfg = {
        "core_asset": testnet_core_asset,
        "gateway_prefix": testnet_gateway_prefix,
        "gateway_distribute_asset": testnet_eth_asset,
        "account": testnet_gateway_account,
        "keys": {"active": testnet_gateway_active, "memo": testnet_gateway_memo},
        "nodes": testnet_bitshares_nodes,
        "gateway_min_deposit": test_gateway_min_deposit,
        "gateway_min_withdrawal": test_gateway_min_withdrawal,
        "gateway_max_deposit": test_gateway_max_deposit,
        "gateway_max_withdrawal": test_gateway_max_withdrawal,
    }


pg_config = {
    "host": os.getenv("DATABASE_HOST"),
    "port": os.getenv("DATABASE_PORT"),
    "user": os.getenv("DATABASE_USERNAME"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "database": os.getenv("DATABASE_NAME"),
}

sql_conn_url = (
    f"postgresql+psycopg2://{pg_config['user']}:{pg_config['password']}"
    f"@"
    f"{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
)

http_config = {"host": os.getenv("HTTP_HOST"), "port": os.getenv("HTTP_PORT")}
