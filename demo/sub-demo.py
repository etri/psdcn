from psdcnv2.clients import Pubsub
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
import asyncio, random, sys

async def sub_test(app, names, seq):
    client = Pubsub(app)
    num_names = len(names)
    while True:
        matched = []
        try:
            for name in names:
                _name = name
                matched += await client.subtopic(name)
            if len(matched) == 0:   # No matches
                print(f"No matches found for {names}")
                await asyncio.sleep(1.0)
                continue
        except (InterestNack, InterestTimeout):
            print(f'Broker unreachable or interest for {_name} timeout')
            await asyncio.sleep(1.0)
            continue
        # Some matches found
        rn_name, dataname = matched[random.randint(0, len(matched)-1)]
        found = False
        count = 3
        # Try 3 times
        while count > 0:
            try:
                data = await client.subdata(rn_name, dataname, seq, lifetime=15000)
                found = True
                print(f"{dataname}[{seq}] is {data}")
                break
            except (InterestNack, InterestTimeout):
                count -= 1
        if not found:
            print(f"{dataname}[{seq}] not found")
        # seq += random.randint(1,10)
        seq += 1
        await asyncio.sleep(0.5)

if __name__ == '__main__':
    app = NDNApp()
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    app.run_forever(after_start=sub_test(app, ["/hello/#", "/adios/+", "/no/#"], start))
