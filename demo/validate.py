# Service token validation example
# The magic word for the service token is 'hasta la vista'
# Usage: validate [<seq_no> [<pub_prefix>]]

from psdcnv3.clients import Pubsub
from ndn.app import NDNApp
import asyncio, random, sys

async def validation_test(app, names, seq, pub_prefix):
    client = Pubsub(app, pub_prefix=pub_prefix)
    for name in names:
        await client.pubadv(name, redefine=False)
        await client.pubdata(name, "Data-" + str(random.randint(1,100)), seq)
    print("[Without service token]")
    matches = await client.subtopic("/test/#")
    for dataname, rn_names in matches.items():
        print(f"{dataname}@{rn_names[-1]}")
    print()
    print("[With valid service token]")
    matches = await client.subtopic("/test/#", servicetoken="hasta la vista")
    for dataname, rn_names in matches.items():
        print(f"{dataname}@{rn_names[-1]}")
    sys.exit()

if __name__ == '__main__':
    app = NDNApp()
    seq = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    pub_prefix = sys.argv[2] if len(sys.argv) > 2 else None
    app.run_forever(after_start=validation_test(app,
        ["/test/validation", "/test/without/validation"], seq, pub_prefix))
