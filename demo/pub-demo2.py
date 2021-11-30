# Repeat publishing 2 to 5 data items in a row for the given names until interrupted
# Usage: pub-demo2 [<seq_no> [<pub_prefix>]]

from psdcnv3.clients import Pubsub
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
import asyncio, random, datetime, sys

async def pub_tests(ps, names, seq, pub_prefix):
    for name in names:
        try:
            await ps.pubadv(name, redefine=False)
        except (InterestNack, InterestTimeout):
            print(f'Broker unreachable or timeout')
            sys.exit()
    while True:
        n_items = random.randint(2, 5)
        try:
            data = ["data_" + str(n) for n in range(seq, seq+n_items)]
            success = True
            for name in names:
                success = success and await ps.pubdata(name, data, seq, seq+n_items-1)
                if success:
                    print(f'Published to {name}[{seq}-{seq+n_items-1}]')
                else:
                    print(f'{name}[{seq}-{seq+n_items-1}]: {ps.reason}')
        except (InterestNack, InterestTimeout):
            print(f'Broker unreachable or interest timeout')
        except Exception as e:
            print(f'{type(e).__name__} {str(e)}')
            ps.app.shutdown()
            break
        finally:
            seq += n_items

if __name__ == "__main__":
    app = NDNApp()
    seq = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    pub_prefix = sys.argv[2] if len(sys.argv) > 2 else None
    ps = Pubsub(app, pub_prefix=pub_prefix)
    app.run_forever(after_start=pub_tests(ps,
        ["/hello", "/adios/psdcnv2", "/nowhere/fast"], seq, pub_prefix))
