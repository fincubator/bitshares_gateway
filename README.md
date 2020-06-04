# BitShares Gateway


## Install
```shell script
git clone https://github.com/fincubator/bitshares_gateway
cd bitshares_gateway/
cp config/config.yml.example config/config.yml
```

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