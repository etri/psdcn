import sys
sys.path.append("../../psdcn")
from broker import localserver
from broker import config

if __name__ == "__main__":
    # API tests
    if not config.loaded():
        config.load()
    print(config.value("forwarder"))
    print(config.value("storage"))

    # Instantiate a Broker as a Local Server
    broker = localserver()
    # Inspect broker internals
    print(broker)

