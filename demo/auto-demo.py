# A client which is both a publisher and a subscriber
# Also shows how to use exclude lists, and fetch the last indexed value.
# Usage: auto-demo [<seq_no> [<pub_prefix>]]

from ndn.app import NDNApp
from psdcnv3.clients import Pubsub
import datetime, sys

async def publish(client, dataname, data, seq):
    if await client.pubadv(dataname, redefine=False):
        print(f"{dataname} advertised")
    return await client.pubdata(dataname, data, seq)

async def subscribe(client, topic, exclude=None):
    matches = await client.subtopic(topic, exclude=exclude)
    if len(matches) == 0:
        return {}
    values = {}
    for (dataname, rn_name) in matches.items():
        data_manis = await client.submani(dataname, rn_name)
        if len(data_manis) > 0:
            node, _, lst = data_manis[-1]  # Last data item of last node
            data = await client.subdata(dataname, lst, node)
            values[f"{dataname}/{lst}"] = data.decode() if data else None
    return values

async def ps_demo(app, seq, pub_prefix):
    # Make a Pubsub client
    client = Pubsub(app, pub_prefix=pub_prefix)
    # Publish some data
    await publish(client, '/a/psdcnv3', 'PSDCNv3 rocks!', seq)
    await publish(client, '/a/python-ndn', 'Thanks to you!', seq)
    await publish(client, '/b/new_world', 'Utopia or Distopia', seq)
    await publish(client, '/b/no/where', 'Nowhere fast', seq)
    pub_data = '{0:%Y/%m/%d %H:%M:%S}'.format(datetime.datetime.now())
    await publish(client, '/c/old/internet', pub_data, seq)
    # Find matches to a topic
    values = await subscribe(client, "/a/+"); print(values)
    values = await subscribe(client, "/b/#", exclude="/b/new_world"); print(values)
    values = await subscribe(client, "/c/+/#"); print(values)
    # Publish some more data
    await publish(client, '/b/b_pictures', f'Nowhere to hide {seq}', seq)
    # Find matches against other topics
    values = await subscribe(client, "/b/#", exclude=["/b/no", "/b/new_world"]); print(values)
    app.shutdown()

if __name__ == "__main__":
    app = NDNApp()
    seq = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    pub_prefix = sys.argv[2] if len(sys.argv) > 2 else None
    app.run_forever(after_start=ps_demo(app, seq, pub_prefix))
