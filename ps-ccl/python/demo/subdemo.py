import sys, random, time
sys.path.append("..")

from psdcnv3 import Pubsub
from ndn.types import InterestTimeout

async def sub_test(ps, topicnames):
    # Subscribe to topics
    ## Continuation functions
    matched = {}
    sub_count = 0
    def onSubSuccess(topicname, manifests):
        nonlocal matched, sub_count
        for dataname in manifests:
            matched[dataname] = manifests[dataname]
        sub_count += 1
    def onSubFailure(topicname, reason):
        print(f"Sub to {topicname} failed. reason: {reason}")
        ps.face.shutdown()
        sys.exit()

    ## Do subscriptions
    for topicname in topicnames:
        ps.subtopic(topicname, onSubSuccess, onSubFailure)
    ## Wait for completion
    while sub_count < len(topicnames):  # Naive polling. Can we do better?
        time.sleep(0.1)

    # Request data manifest and fetch data
    def onManiSuccess(dataname, manifest):
        rn_name, _, seq = manifest
        try:
            while True:
                try:
                    ## Fetch data for the given seq#
                    data = ps.subdata(dataname, seq, rn_name, lifetime=10_000)
                    print(f"{dataname}[{seq}] is {bytes(data).decode()}")
                except InterestTimeout:
                    print(f"{dataname}[{seq}] ??")
                if random.random() > 0.5:
                    time.sleep(random.random()/10)
                seq += 1
        except KeyboardInterrupt:
            pass
        ps.face.shutdown()
    def onManiFailure(dataname, reason):
        print(f"Manifest for {dataname} not fetched, reason: {reason}")
        ps.face.shutdown()

    if len(matched) > 0:
        dataname, rn_names = list(matched.items())[random.randint(0, len(matched)-1)]
        ps.submani(dataname, rn_names[-1], onManiSuccess, onManiFailure)
    else:
        print(f"No matches found for {topicnames}")
        ps.face.shutdown()
        sys.exit()

from ndn.app import NDNApp
if __name__ == "__main__":
    app = NDNApp()
    svc_name = "/dcn/psdcn"
    app.run_forever(
        after_start=sub_test(Pubsub(app, svc_name=svc_name), ["/hello/#", "/adios/+", "/nowhere/#"])
    )
