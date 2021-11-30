# Publisher-storage variation of auto-demo
# Usage: pub-publisher [<seq_no> [<pub_prefix> [>do_pub>]]]

from psdcnv3.clients import Pubsub
from psdcnv3.psk import StorageType
from ndn.app import NDNApp
import datetime, sys

async def pub_pub(ps, dataname, storagetype=StorageType.BROKER, storageprefix=None):
    if storageprefix is None:
        if await ps.pubadv(dataname, redefine=True):
            print(f"{dataname} advertised")
        else:
            print(f"{dataname} not advertised. ({ps.reason})")
    elif await ps.pubadv(dataname,
            storagetype=storagetype, storageprefix=storageprefix, redefine=True):
        print(f"{dataname} advertised")
    else:
        print(f"{dataname} not advertised. ({ps.reason})")

async def publish(ps, dataname, data, seq):
    if await ps.pubdata(dataname, data, seq):
        print(f"Publication to {dataname} succeeded")
    else:
        print(f"Publication to {dataname} failed. ({ps.reason})")

async def ps_demo(app, seq, pub_prefix, do_pub):
    # Make a Pubsub client
    ps = Pubsub(app, pub_prefix=pub_prefix)
    # Advertise some names for which publisher will provide data
    await pub_pub(ps, '/pa/see/what/will/happen')
    await pub_pub(ps, '/pa/pub/will/publish', StorageType.PUBLISHER, storageprefix='/pubstorage-1')
    await pub_pub(ps, '/pa/DIFS/will/publish', StorageType.DIFS, storageprefix='/difs:0:1')
    if do_pub:
    	pub_data = '{0:%Y/%m/%d %H:%M:%S}'.format(datetime.datetime.now())
    	await publish(ps, '/pa/see/what/will/happen', pub_data, seq)
    	await publish(ps, '/pa/pub/will/publish', pub_data, seq)
    app.shutdown()

if __name__ == "__main__":
    app = NDNApp()
    seq = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    pub_prefix = sys.argv[2] if len(sys.argv) > 2 else None
    app.run_forever(after_start=ps_demo(app, seq, pub_prefix, len(sys.argv) > 3))
