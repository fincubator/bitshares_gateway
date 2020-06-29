# BitShares Gateway

[![License]][LICENSE]
[![Telegram]][Telegram join]
![build](https://github.com/fincubator/bitshares_gateway/workflows/build/badge.svg)
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
git clone https://github.com/fincubator/bitshares_gateway
cd bitshares_gateway
```

Create gateway config file and fill it with your data. If not, gateway will start in testnet with
parameters from tests dir.
```bash
cp config/gateway.yml.example config/gateway.yml
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
>Why not docker-compose up command?'
>> Because on production we need some interactive shell to input keys/password

#### Running in testnet
```bash
sudo docker-compose up --build -d
```
Will be using test account from test fixtures

# How it works
BitShares Gateway serve SINGLE bitshares asset. 
It means that if you want to run `Bitcoin/BITSHARES.BITCOIN_ASSET` exchange, you need to deploy 3 instances:
1. This project (configured to work with BITSHARES.BITCOIN_ASSET)
2. [Booker]
3. Some Bitcoin gateway that can interact with [Booker] api

Also it means that if you want to run 10 cryptocurrency exchanges, you need 10 instances of BitShares Gateway, 10 coin (Native) 
gateways and one [Booker]

`Gateway` class in `gateway.py` file is heart of project logic. It is still in development.

There is `bitshares_utils.py` module - useful async python tools allow to build gateway's algorithms.
##### Using bitshares_utils:


```python
# Simple example to issue some asset

import asyncio

from bitshares_utils import *

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
[Booker]: https://github.com/fincubator/booker
[BitShares Core]: https://github.com/bitshares/bitshares-core
[Code style: black]: https://img.shields.io/badge/code%20style-black-000000.svg
[black code style]: https://github.com/psf/black