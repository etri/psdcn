# Test cases of Patterns/Subscriptions implementations

import sys
sys.path.append("../../../psdcnv2")
from datetime import datetime
from names import TrieNames, ProcNames, RegexpNames

if __name__ == "__main__":
    impl = ("trie" if len(sys.argv) < 2 else sys.argv[1]).capitalize()
    handler = {'Trie': TrieNames(), 'Proc': ProcNames(), 'Regexp': RegexpNames()}[impl]
    print("Using", impl, "\n")

    names = [
        "/hello/a/b/c", "/hello", "/hello/a/c", "/hello/1/v/2", "/hello/x/v/z", "/world/cup",
        "/natasha/mangdor", "/worldcup/2018", "/hello/a/b",
    ]
    for dataname in names:
       handler.advertise("rn1", dataname)
    print("Advertisements made so far...")
    for node in handler.advertisements():
        print("\t", node.dataname)
    print()

    unadv = ["/hello/a/c", "/worldcup/2018"]
    print("Unadvertizing", unadv)
    for dataname in unadv:
        handler.unadvertise(dataname)
    newadv = ["/hello/etri/psdcn", "/world/cup", "/nowhere/fast"]
    print("Advertising", newadv)
    for dataname in newadv:
        handler.advertise("rn2", dataname)
    for node in handler.advertisements():
        print("\t", node.dataname)
    print()

    topic_1 = "/hello/a/+/+"
    print("Testing topic:", topic_1)
    for node in handler.matches(topic_1):
        print("Found a match:", node.rn_name, node.dataname)
    print()

    print("Testing topic:", topic_1)
    for node in handler.matches(topic_1):
        print("Found a match:", node.rn_name, node.dataname)
    print()

    topic_2 = "/hello/+/v/+"
    print("Testing topic:", topic_2)
    for node in handler.matches(topic_2):
        print("Found a match:", node.rn_name, node.dataname)
    print()

    topic_3 = "/hello/+/#"
    print("Testing topic:", topic_3)
    for node in handler.matches(topic_3):
        print("Found a match:", node.rn_name, node.dataname)
    print()

    topic_4 = "/hello/#"
    print("Testing topic:", topic_4)
    for node in handler.matches(topic_4):
        print("Found a match:", node.rn_name, node.dataname)
    print()

    topic_5 = "/#"
    print("Testing topic:", topic_5)
    for node in handler.matches(topic_5):
        print("Found a match:", node.rn_name, node.dataname)
    print()
