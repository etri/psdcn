from psdcnv2.clients import Pubsub
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
import asyncio, random, datetime, sys

async def pub_tests(app, names, seq):
    client = Pubsub(app)
    for name in names:
        try:
            await client.pubadv(name, redefine=False)
        except (InterestNack, InterestTimeout):
            print('Broker unreachable or interest timeout')
            sys.exit()
    while True:
        try:
            for name in names:
                data = '{0:%Y/%m/%d %H:%M:%S}'.format(datetime.datetime.now())
                await client.pubdata(name, data, seq)
                print(f'Published {data} to {name}[{seq}]')
            seq += 1
        except (InterestNack, InterestTimeout):
            print('Broker unreachable or interest timeout')
            await asyncio.sleep(1)
        except Exception as e:
            print(f'{type(e).__name__} {str(e)}')
        finally:
            pass
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    app = NDNApp()
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    app.run_forever(after_start=pub_tests(app,
        ["/hello", "/adios/psdcnv1", "/byebye"], start))
