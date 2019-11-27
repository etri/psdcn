import sys
sys.path.append("../../psdcn")
from broker import LocalServer
from topics import Trie, Proc
from storage import MemoryStorage, RedisStorage, ProtocolHandler

if __name__ == "__main__":
    # Instantiate a Broker as a Local Server
    broker = LocalServer(Trie(), MemoryStorage())

    # Advertise datanames
    commands = [
        "/rn/pubadv/etri/bldg7/room513/temperature",
        "/rn/pubadv/etri/bldg7/room513/switches",
        "/rn/pubadv/etri/bldg7/room210/printers",
        "/rn/pubadv/etri/bldg7/room303/temperature",
        "/rn/pubadv/presidential/election/2022/candidates",
        "/rn/pubadv/etri/bldg3/room628/switches",
        "/rn/pubadv/etri/bldg3/room628/temperature",
        "/rn/pubadv/etri/bldg3/room628/printers",
        "/rn/pubunadv/etri/bldg3/room628/switches",
    ]
    for command in commands:
        broker.handle(command)
    print "Advertise/Unadvertise 8/1 datanames..."
    print

    # *-- Added per ETRI's request on Nov. 5th --*
    # List Datanames advertised so far.
    # ProtocolHandler is wire procotol handler for RedisStorage
    # which is general enough to handle packaging datanames in a list and
    # pass thru the wire (encode), and decoding back again as a list
    datanames = ProtocolHandler().handle_request(broker.handle("/rn/listnames"))
    print 'Datanames advertised so far...'
    for (name, rn) in datanames:
        print "    ", name, '@' + rn
    print

    # Publishing Some Data
    print "Publishing data..."
    pubdata = [
        ("/rn/pubdata/etri/bldg7/room513/temperature/1", 28.5),
        ("/rn/pubdata/etri/bldg7/room513/temperature/2", 28.2),
        ("/rn/pubdata/etri/bldg7/room513/temperature/3", 28.0),
        ("/rn/pubdata/etri/bldg7/room303/temperature/1", 29.0),
        ("/rn/pubdata/etri/bldg7/room210/printers/1", {'color': ['hp'], 'bw': ['canon', 'epson']})
    ]
    for command, value in pubdata:
        parts = command.split("/")[1:]
        print "    ", "/" + ('/'.join(parts[2:])), '=', value, "@" + parts[0]
        broker.handle(command, value)
    print

    # Check if publication has been done properly
    # print broker._storage.get("/etri/bldg7/room513/temperature")
    # print broker._storage.get("/etri/bldg7/room210/printers")
    # print

    # Manifest Topic Request
    topic = "/rn/manitopic/etri/bldg7/+/temperature"
    print 'Data names for topic', topic, 'are...'
    subscrs = broker.handle(topic)
    for dataname in subscrs:
        print "    ", dataname
    print

    # Manifest Data Request
    data_manifests = [(dataname, broker.handle("/rn/manidata" + dataname))
        for dataname in subscrs]
    print 'Data manifests for corresponding names are...'
    for (dataname, last_index) in data_manifests:
        print "    ", dataname,'=', last_index
    print

    # Unread Data Request
    print 'Data for the manifests starting from index 2 are...'
    for dataname, _ in data_manifests:
        data_delivered = broker.handle("/rn/subdata" + dataname, 2)
        print "    ", dataname, data_delivered
    print
    
    # Log Data Request
    print 'All data items for the manifests are...'
    for dataname, _ in data_manifests:
        data_delivered = broker.handle("/rn/subdata" + dataname, 1)
        print "    ", dataname, data_delivered
    print
    
    # The End
    print "That's all, folks!"

