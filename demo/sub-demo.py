# Subscriber demo
# Usage: sub-demo

from psdcnv3.clients import Pubsub
from ndn.app import NDNApp
import asyncio, random, sys

async def sub_test(ps, topicnames):
    matched = {}
    try:
        for topicname in topicnames:
            matches = await ps.subtopic(topicname)
            for dataname in matches:
                matched[dataname] = matches[dataname]
        if len(matched) == 0:   # No matches
            print(f"No matches found for {topicnames}")
            sys.exit()
    except:
        print(f'Broker unreachable or interest timeout')
        sys.exit()
    # Matches found. Pick one match randomly and asks for data manifests
    dataname, rn_names = list(matched.items())[random.randint(0, len(matched)-1)]
    manifest = await ps.submani(dataname, rn_names[-1])
    await fetch_data(ps, dataname, manifest)

async def fetch_data(ps, dataname, manifest):
    rn_name, _, seq = manifest
    while True:
        try:
            data = await ps.subdata(dataname, seq, rn_name, lifetime=10_000)
            print(f"{dataname}[{seq}] is {bytes(data).decode()}")
        except:
            print(f"{dataname}[{seq}] ??")
            ps.app.shutdown()
            break
        if random.random() > 0.5:
            await asyncio.sleep(random.random()/10)
        seq += 1

if __name__ == '__main__':
    app = NDNApp()
    app.run_forever(after_start=sub_test(Pubsub(app), ["/hello/#", "/adios/+", "/nowhere/#"]))
