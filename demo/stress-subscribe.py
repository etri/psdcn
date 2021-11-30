# Subscribe to datanames
# Usage: stress-subscribe <num-names>

from psdcnv3.clients import Pubsub
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
import sys

async def subtopic_tests(ps, num_names):
    count = 0
    for i in range(num_names):
        try:
            name = "dataname_" + str(i)
            if await ps.subtopic(name):
                count += 1
            # if (i+1) % 500 == 0:
            #     print(f'Subscribed to {i+1} names')
        except (InterestNack, InterestTimeout):
            print('Broker unreachable or interest timeout')
            # await asyncio.sleep(1)
        except Exception as e:
            print(f'{type(e).__name__} {str(e)}')
    print(f"{count} out of {num_names} processed.")
    ps.app.shutdown()

if __name__ == "__main__":
    app = NDNApp()
    num_names = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    ps = Pubsub(app)
    app.run_forever(after_start=subtopic_tests(ps, num_names))
