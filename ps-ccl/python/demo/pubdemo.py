import sys, datetime, time
sys.path.append("..")

from psdcnv3 import Pubsub

async def pub_tests(ps, names, seq):
    # Advertise names
    ## Continuation functions
    adv_count = 0
    def onAdvSuccess(dataname):
        nonlocal adv_count
        adv_count += 1
    def onAdvFailure(dataname, reason):
        print(f"Unable to advertise {dataname}, {reason}")
        ps.face.shutdown()
        sys.exit()
    ## Do advertise
    for name in names:
        ps.pubadv(name, onAdvSuccess, onAdvFailure, {'redefine': True})
    ## Wait for completion
    while adv_count < len(names):   # Naive polling. Can we do better?
        time.sleep(0.1)

    # Publish data items
    ## Continuation functions
    def onPubSuccess(dataname, seq):
        print(f'Published to {dataname}[{seq}]')
    def onPubFailure(dataname, seq, reason):
        print(f"Unable to publish to {dataname}/{seq}, {reason}")

    ## Run until CTRL-C is hit
    try:
        while True:
            for name in names:
                data = '{0:%Y/%m/%d %H:%M:%S}'.format(datetime.datetime.now())
                ps.pubdata(name, seq, data, onPubSuccess, onPubFailure)
            seq += 1
    except KeyboardInterrupt:
        pass
    ps.face.shutdown()
    # sys.exit()
    
from ndn.app import NDNApp
if __name__ == "__main__":
    app = NDNApp()
    svc_name = "/dcn/psdcn"
    ps = Pubsub(app, svc_name=svc_name, pub_prefix=sys.argv[2] if len(sys.argv) > 2 else None)
    app.run_forever(after_start=pub_tests(ps,
        ["/hello", "/adios/psdcnv2", "/nowhere/fast"],
        seq=int(sys.argv[1]) if len(sys.argv) > 1 else 1
    ))
