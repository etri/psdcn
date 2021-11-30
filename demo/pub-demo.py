# Repeat publishing data items for the given names until interrupted
# Usage: pub-demo [<seq_no> [<pub_prefix>]]

from psdcnv3.clients import Pubsub
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
import asyncio, datetime, sys

async def pub_tests(ps, names, seq, pub_prefix):
    for name in names:
        try:
            await ps.pubadv(name, redefine=False)
        except (InterestNack, InterestTimeout):
            print('Broker unreachable or interest timeout')
            sys.exit()
    while True:
        try:
            for name in names:
                data = '{0:%Y/%m/%d %H:%M:%S}'.format(datetime.datetime.now())
                sent = await ps.pubdata(name, data, seq)
                if sent:
                    print(f'Published {data} to {name}[{seq}]')
                else:
                    print(f'{name}: {ps.reason}')
            seq += 1
        except (InterestNack, InterestTimeout):
            print('Broker unreachable or interest timeout')
            # await asyncio.sleep(1)
        except Exception as e:
            print(f'{type(e).__name__} {str(e)}')
            ps.app.shutdown()
            break
        finally:
            pass

if __name__ == "__main__":
    app = NDNApp()
    seq = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    pub_prefix = sys.argv[2] if len(sys.argv) > 2 else None
    ps = Pubsub(app, pub_prefix=pub_prefix)
    app.run_forever(after_start=pub_tests(ps,
        ["/hello", "/adios/psdcnv2", "/nowhere/fast"], seq, pub_prefix))
