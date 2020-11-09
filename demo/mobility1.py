from psdcnv2.clients import Pubsub
from psdcnv2.psk import TopicScope
from ndn.app import NDNApp
import datetime

async def publish(client, dataname, data, seq):
    if await client.pubadv(dataname, redefine=False):
        print(f"{dataname} advertised")
    return await client.pubdata(dataname, data, seq)

async def subscribe(client, topic, exclude=None, seq=0):
    matches = await client.subtopic(topic, exclude=exclude)
    if len(matches) == 0:
        return {}
    seq = int(seq)
    _values = {}
    for (rn_name, dataname) in matches:
        _, lst, _, _ = await client.submani(rn_name, dataname)
        if lst > 0:
            data = await client.subdata(rn_name, dataname, seq)     # last element
            _idx = seq if seq > 0 else lst + seq
            _values[f"{dataname}[{_idx}]"] = data
    return _values

async def ps_demo(app):
    # Make a Pubsub client
    client = Pubsub(app)
    # Publish some data
    await publish(client, '/b/new_world', 'Utopia or Distopia-1', 1)
    await publish(client, '/b/new_world', 'Utopia or Distopia-2', 2)
    await publish(client, '/b/new_world', 'Utopia or Distopia-3', 3)
    await publish(client, '/b/no/where', 'Nowhere fast-1', 1)
    await publish(client, '/b/no/where', 'Nowhere fast-2', 2)
    # Find matches to a topic
    values = await subscribe(client, "/b/#"); print(values)

    app.shutdown()

if __name__ == "__main__":
    app = NDNApp()
    app.run_forever(after_start=ps_demo(app))
