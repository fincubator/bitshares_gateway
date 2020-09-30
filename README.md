# BitShares Gateway

[![License]][LICENSE]
[![Telegram]][Telegram join]
![build](https://github.com/fincubator/bitshares_gateway/workflows/build/badge.svg)
![pre-commit](https://github.com/fincubator/bitshares_gateway/workflows/pre-commit/badge.svg)
[![Code style: black]][black code style]

Microservice receiving and sending payments in BitShares blockchain.
Work with [Booker].

## Install
### Linux (Ubuntu 18.04)
#### Install with Docker
##### Requirements
* [Docker]
* [Docker Compose]

Install dependencies
```bash
sudo apt install git docker.io docker-compose
```

Clone the repository:
```bash
git clone --recurse-submodules https://github.com/fincubator/bitshares_gateway
cd bitshares_gateway
```

Create gateway config file and fill it with your data. If not, gateway will start in testnet with testing
parameters.
```bash
cp gateway.yml.example gateway.yml
```

Create test *.env* file
```bash
cp .env.example .env
```

## Run
#### Run on production (mainnet)
```bash
sudo docker-compose run -d postgres
sudo docker-compose run gateway
```
>Why not 'docker-compose up' command?
>> Because on production we need some interactive shell to input keys/password

#### Running in testnet
```bash
sudo docker-compose up --build -d
```
Will be using default test account

# How it works
BitShares Gateway serve SINGLE bitshares asset.
It means that if you want to run `Bitcoin/BITSHARES.BITCOIN_ASSET` exchange, you need to deploy 3 instances:
1. This project (configured to work with BITSHARES.BITCOIN_ASSET)
2. [Booker]
3. Some Bitcoin gateway that can interact with [Booker] API

Also it means that if you want to run 10 cryptocurrency exchanges, you need 10 instances of BitShares Gateway, 10 coin (Native)
gateways and one [Booker]

`Gateway` class in `src/gateway.py` file is a heart of project logic. It is still in development.

##### Using bitshares_utils:
There is `src/bitshares_utils.py` module - useful async python tools over [Pybitshares] allow to build gateway's algorithms
simple and fast.

```python
# Simple example to issue some asset

import asyncio

from src.blockchain.bitshares_utils import *

async def issue_loop_example():
    """Setup bitshares instance"""
    await init_bitshares(node="wss://your.node",
                        account="your_account_name",
                        keys=["5Ksk..YouMemoKey", "5Ksk..YouActiveKey"],)

    # Non broadcasted transaction
    pre_tx = await asset_issue("your.bitshares.name", 10, "FINTEH.USDT")

    """Doing your stuff"""

    # Broadcast now!
    await broadcast_tx(pre_tx)


asyncio.run(issue_loop_example())
```

#### Tests
BitShares Gateway has unit tests that can be run with [Pytest] framework. It's running actuomatically on every push in Github Actions.

To run it manually, execute inside `gateway` container:
```shell script
pipenv install --dev
pipenv run pytest
```

##### Where is gateway wallet account private keys?
Wallet account's keys stored as base64-encoded strings in file `.accountname.keys`.
This file will be created after first run with filled `gateway.yml` file.

Example:
```
active:AwGvBZbCr2mzIcPkrUP+o0ATpghI5IyzztfYYKOfofafb/M3KVKCnD7qL0ImUrDLK2/9oM7HyDNhrshIZyn/680on21QNYYmRbueXNyNcw6kX1YQNQfNdIX6eAWXQTy201d+O60Ggy2Jnco6wpf/oU9nAWNPzXKFVK/EZNS/TGDGrA==
memo:AwGG1vYvBmQp3dX6pFz1tQ/25y1vwCdtbOXP3JijGTVOw69OEu1+dHYgrDjFEPdeRmKWOX8WIvFqK7tUZ/ZPevmAZUxxQfExj2PLJAdAO632k0XKVEEUXyWDuzUbfH6+OINaWl4mDicNH6rZOCBd5LSdSmjwT+FsD53ZAvrBJWj44Q==
```

# Contributing
You can help by working on opened issues, fixing bugs, creating new features or
improving documentation.

Before contributing, please read [CONTRIBUTING.md] first.

# License
Bitshares Gateway is released under the GNU Affero General Public License v3.0. See
[LICENSE] for the full licensing condition

[License]: https://img.shields.io/github/license/fincubator/bitshares_gateway
[LICENSE]: LICENSE
[CONTRIBUTING.md]: CONTRIBUTING.md
[Telegram]: https://img.shields.io/badge/Telegram-fincubator-blue?logo=telegram
[Telegram join]: https://t.me/fincubator
[Docker]: https://www.docker.com
[Docker Compose]: https://www.docker.com
[Pytest]: https://docs.pytest.org/en/stable/
[Booker]: https://github.com/fincubator/booker
[Pybitshares]: https://github.com/bitshares/python-bitshares
[BitShares Core]: https://github.com/bitshares/bitshares-core
[Code style: black]: https://img.shields.io/badge/code%20style-black-000000.svg
[black code style]: https://github.com/psf/black
