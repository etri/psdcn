# Advertise a bulk of datanames
# Usage: stress-advertise <num-names>

from psdcnv3.clients import Pubsub
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
import asyncio, random, datetime, sys

async def adv_tests(ps, num_names):
    for i in range(num_names):
        try:
            name = "dataname_" + str(i)
            await ps.pubadv(name)
            if (i+1) % 100 == 0:
                print(f'Advertised {i+1} names')
        except (InterestNack, InterestTimeout):
            print('Broker unreachable or interest timeout')
            # await asyncio.sleep(1)
        except Exception as e:
            print(f'{type(e).__name__} {str(e)}')
        finally:
            pass
    ps.app.shutdown()

if __name__ == "__main__":
    app = NDNApp()
    num_names = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    ps = Pubsub(app)
    app.run_forever(after_start=adv_tests(ps, num_names))
