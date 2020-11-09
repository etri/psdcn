# Publisher-storage and Local-topicscope variation of auto-demo

from psdcnv2.clients import Pubsub
from psdcnv2.psk import StorageType, TopicScope
from ndn.app import NDNApp
import datetime


async def pub_pub(client, dataname, prefix=None):
    if prefix is None:
        if await client.pubadv(dataname, redefine=True):
            print(f"{dataname} advertised")
        else:
            print(f"{dataname} not advertised")
    elif await client.pubadv(dataname, StorageType.PUBLISHER, pubprefix=prefix, redefine=True):
        print(f"{dataname} advertised")
    else:
        print(f"{dataname} not advertised")

async def publish(client, dataname, data):
    if await client.pubdata(dataname, data):
        print(f"Publication to {dataname} succeeded")
    else:
        print(f"Publication to {dataname} failed")

async def ps_demo(app):
    # Make a Pubsub client
    # client = Pubsub(app, scope=TopicScope.LOCAL)
    client = Pubsub(app)
    # Advertise some names for which publisher will provide data
    await pub_pub(client, '/pa/pub/will/publish', prefix='/pub-1')
    await pub_pub(client, '/pa/see/what/will/happen')
    pub_data = '{0:%Y/%m/%d %H:%M:%S}'.format(datetime.datetime.now())
    await publish(client, '/pa/see/what/will/happen', pub_data)
    await publish(client, '/pa/pub/will/publish', pub_data)
    print(await client.subtopic('/pa/pub/+/publish'))
    print(await client.subtopic('/pa/#'))
    app.shutdown()

if __name__ == "__main__":
    app = NDNApp()
    app.run_forever(after_start=ps_demo(app))

