# BitShares Gateway


## Install
```shell script
git clone https://github.com/fincubator/bitshares_gateway
cd bitshares_gateway/
```

##### Using bitshares_utils:

```python
# Simple example to issue some 
import asyncio

from bitshares_utils import *
from config import cfg

async def gateway_loop_example():
    """Setup bitshares instance"""
    await init_bitshares(node="wss://your.node",
                        gateway_account="your_account_name",
                        keys=["5Ksk..YouMemoKey", "5Ksk..YouActiveKey"],)
    
    # Non broadcasted transaction
    pre_tx = await asset_issue("bitcrab", 10, 'FINTEH.USDT')
    
    """Doing your stuff"""    

    # Broadcast now!
    await broadcast_tx(pre_tx)


asyncio.run(gateway_loop_example())
```