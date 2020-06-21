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

Start the gateway as daemon by running the command:
```bash
sudo docker-compose up --build -d
```

# How it works
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