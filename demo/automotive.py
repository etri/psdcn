from psdcnv2.clients import Pubsub
from psdcnv2.psk import StorageType, TopicScope
from ndn.app import NDNApp
import datetime

async def publish(client, dataname, data):
    if await client.pubadv(dataname, redefine=False):
        print(f"{dataname} advertised")
    return await client.pubdata(dataname, data)

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
    await publish(client, '/a/psdcnv2', 'PSDCNv2')
    await publish(client, '/a/psdcnv2', 'Rocks!')
    await publish(client, '/a/python-ndn', 'Thanks!')
    await publish(client, '/b/new_world', 'Utopia or Distopia')
    await publish(client, '/b/no/where', 'Nowhere fast')
    await publish(client, '/a/psdcnv2', 'Rocks!')
    pub_data = '{0:%Y/%m/%d %H:%M:%S}'.format(datetime.datetime.now())
    await publish(client, '/c/old/internet', pub_data)
    # Find matches to a topic
    values = await subscribe(client, "/a/+"); print(values)
    values = await subscribe(client, "/b/#", exclude="/b/no"); print(values)
    values = await subscribe(client, "/c/+/#"); print(values)
    # Publish some more data
    await publish(client, '/b/b_pictures', 'Nowhere to hide')
    # Find matches again to other topics
    values = await subscribe(client, "/a/+"); print(values)
    values = await subscribe(client, "/b/#", exclude="/b/new_world"); print(values)
    values = await subscribe(client, "/c/+/#"); print(values)
    app.shutdown()

if __name__ == "__main__":
    app = NDNApp()
    app.run_forever(after_start=ps_demo(app))
