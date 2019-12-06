import sys
sys.path.append("../../psdcn")
from broker import LocalServer
from topics import Trie, Proc
from storage import MemoryStorage, RedisStorage

if __name__ == "__main__":
    # Instantiate a Broker as a Local Server
    broker = LocalServer(Trie(), MemoryStorage())

    # Advertise datanames
    print("Advertising datanames...")
    commands = [
        "/rn1/pubadv/etri/bldg7/room513/temperature",
        "/rn1/pubadv/etri/bldg7/room513/switches",
        "/rn1/pubadv/etri/bldg7/room210/printers",
        "/rn1/pubadv/etri/bldg7/room303/temperature",
        "/rn1/pubadv/presidential/election/2022/candidates",
        "/rn1/pubadv/etri/bldg3/room628/switches",
        "/rn2/pubadv/etri/bldg3/room628/temperature",
        "/rn2/pubadv/etri/bldg3/room628/printers",
        "/rn1/pubunadv/etri/bldg3/room628/switches",
    ]
    for command in commands:
        broker.handle(command)
    for dataname, rn_name in broker._datanames.advertisements():
        print("    ", dataname, "@" + rn_name)
    print()

    # Publishing Some Data
    print("Publishing data...")
    pubdata = [
        ("/rn1/pubdata/etri/bldg7/room513/temperature/1", 28.5),
        ("/rn1/pubdata/etri/bldg7/room513/temperature/2", 28.2),
        ("/rn1/pubdata/etri/bldg7/room513/temperature/3", 28.0),
        ("/rn1/pubdata/etri/bldg7/room303/temperature/1", 29.0),
        ("/rn1/pubdata/etri/bldg7/room210/printers/1", {'color': ['hp'], 'bw': ['canon', 'epson']})
    ]
    for command, value in pubdata:
        parts = command.split("/")[1:]
        print("    ", "/" + ('/'.join(parts[2:])), '=', value, "@" + parts[0])
        broker.handle(command, value)
    print()

    # Check if publication has been done properly
    # print(broker._storage.get("/etri/bldg7/room513/temperature"))
    # print(broker._storage.get("/etri/bldg7/room210/printers"))
    # print()

    # Manifest Topic Request
    topic = "/rn1/manitopic/etri/bldg7/+/temperature"
    print('Data names for topic', topic, 'are...')
    subscrs = broker.handle(topic)
    for dataname in subscrs:
        print("    ", dataname)
    print()

    # Manifest Data Request
    data_manifests = [(dataname, broker.handle("/rn1/manidata" + dataname))
        for dataname in subscrs]
    print('Data manifests for corresponding names are...')
    for (dataname, last_index) in data_manifests:
        print("    ", dataname,'=', last_index)
    print()

    # Unread Data Request
    print('Data for the manifests starting from index 2 are...')
    for dataname, _ in data_manifests:
        data_delivered = broker.handle("/rn1/subdata" + dataname, 2)
        print("    ", dataname, data_delivered)
    print()
    
    # Log Data Request
    print('All data items for the manifests are...')
    for dataname, _ in data_manifests:
        data_delivered = broker.handle("/rn1/subdata" + dataname, 1)
        print("    ", dataname, data_delivered)
    print()
    
    # The End
    print("That's all, folks!")

