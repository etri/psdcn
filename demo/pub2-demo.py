from psdcnv2.clients import Pubsub
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
import asyncio, random, datetime, sys

async def pub2_tests(app, names, seq):
    client = Pubsub(app, id='/pub1')
    for name in names:
        try:
            await client.pubadv(name, redefine=False)
        except (InterestNack, InterestTimeout):
            print(f'Broker unreachable or timeout')
            sys.exit()
    while True:
        n_items = random.randint(2, 5)
        try:
            data = ["data_" + str(n) for n in range(seq, seq+n_items)]
            success = True
            for name in names:
                await asyncio.sleep(0.3)
                success = success and await client.pubdata2(name, data, seq, seq+n_items-1)
            if success:
                print(f'Published to {names}[{seq}~{seq+n_items-1}]')
            else:
                print(f'Failed to publish {names}[{seq}~{seq+n_items-1}]')
        except (InterestNack, InterestTimeout):
            print(f'Broker unreachable or interest timeout')
            await asyncio.sleep(1)
        except Exception as e:
            print(f'{type(e).__name__} {str(e)}')
        finally:
            seq += n_items
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    app = NDNApp()
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    app.run_forever(after_start=pub2_tests(app,
        ["/hello", "/adios/psdcnv1", "/byebye"], start))
