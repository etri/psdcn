# Test cases of Patterns/Subscriptions implementations

import sys
sys.path.append("../../psdcn")
from topics import Trie, Proc, Regexp

if __name__ == "__main__":
    impl = ("trie" if len(sys.argv) < 2 else sys.argv[1]).capitalize()
    handler = {'Trie': Trie(), 'Proc': Proc(), 'Regexp': Regexp()}[impl]
    print "Using", impl, "\n"

    names = [
        "/hello/a/b/c", "/hello", "/hello/a/c", "/hello/1/v/2", "/hello/x/v/z", "/world/cup",
        "/natasha/mangdor", "/worldcup/2018", "/hello/a/b",
    ]
    for dataname in names:
       handler.advertise(dataname, "rn1")
    print "Advertisements made so far..."
    for dataname in handler.advertisements():
        print "\t", dataname
    print

    unadv = ["/hello/a/c", "/worldcup/2018"]
    print "Unadvertizing", unadv
    for dataname in unadv:
        handler.unadvertise(dataname)
    newadv = ["/hello/etri/psdcn", "/world/cup", "/nowhere/fast"]
    print "Advertising", newadv
    for dataname in newadv:
        handler.advertise(dataname, "rn2")
    for dataname in handler.advertisements():
        print "\t", dataname
    print

    topic_1 = "/hello/a/+/+"
    print "Testing topic:", topic_1
    for v in handler.matches(topic_1):
        print "Found a match:", v.dataname, v.rn_name
    print

    topic_2 = "/hello/+/v/+"
    print "Testing topic:", topic_2
    for v in handler.matches(topic_2):
        print "Found a match:", v.dataname, v.rn_name
    print

    topic_3 = "/hello/+/#"
    print "Testing topic:", topic_3
    for v in handler.matches(topic_3):
        print "Found a match:", v.dataname, v.rn_name
    print

    topic_4 = "/hello/#"
    print "Testing topic:", topic_4
    for v in handler.matches(topic_4):
        print "Found a match:", v.dataname, v.rn_name
    print

