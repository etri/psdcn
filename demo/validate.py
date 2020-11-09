from psdcnv2.clients import Pubsub
from ndn.app import NDNApp
import asyncio, random, sys

async def validation_test(app, names):
    client = Pubsub(app)
    for name in names:
        await client.pubadv(name, redefine=True)
        await client.pubdata(name, "Data-" + str(random.randint(1,100)))
    print("[Without service token]")
    matches = await client.subtopic("/test/#")
    for rn_name, dataname in matches:
        print(f"{dataname}@{rn_name}")
    print()
    print("[With valid service token]")
    matches = await client.subtopic("/test/#", servicetoken="hasta la vista")
    for rn_name, dataname in matches:
        print(f"{dataname}@{rn_name}")
    sys.exit()

if __name__ == '__main__':
    app = NDNApp()
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    app.run_forever(after_start=validation_test(app,
        ["/test/validation", "/test/without/validation"]))

