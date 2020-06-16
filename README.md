# BitShares Gateway

[![License]][LICENSE.md]
[![Telegram]][Telegram join]


Microservice receiving and sending payments in BitShares blockchain. 
Depends on [Booker]

## Install
#### Manually
```shell script
git clone https://github.com/fincubator/bitshares_gateway
cd bitshares_gateway/
cp config/config.yml.example config/config.yml
# fill config.yml with your values
python3 -m pipenv shell
pipenv install
python3 .
```

#### With  Docker

Install git, Docker, Docker Compose:
```bash
sudo apt install git docker.io docker-compose
```

Clone the repository:
```bash
git clone https://github.com/fincubator/booker
cd booker
```

Start the services by running the command:
```bash
sudo docker-compose up
```


# Contributing
You can help by working on opened issues, fixing bugs, creating new features or
improving documentation.

Before contributing, please read [CONTRIBUTING.md] first.

# License
Booker is released under the GNU Affero General Public License v3.0. See
[LICENSE.md] for the full licensing condition.


## How it works

Add some BitShares nodes to `config.yml` file.
Highly recommend to deploy your own [BitShares Core]. 

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


[License]: https://img.shields.io/github/license/fincubator/bitshares_gateway
[LICENSE.md]: LICENSE.md
[CONTRIBUTING.md]: CONTRIBUTING.md
[Telegram]: https://img.shields.io/badge/Telegram-fincubator-blue?logo=telegram
[Telegram join]: https://t.me/fincubator
[Docker]: https://www.docker.com
[Docker Compose]: https://www.docker.com
[Booker]: https://github.com/fincubator/booker
[BitShares Core]: https://github.com/bitshares/bitshares-core