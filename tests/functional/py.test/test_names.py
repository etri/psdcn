"""
Names-related tests
"""

import sys
sys.path.append("../../..")

from random import randint
from datetime import datetime
from psdcnv3.names import TrieNames, ProcNames, RegexpNames

def test_instances():
    """
    Tests if Names implementations can make instances correctly.
    """
    names_0 = TrieNames()
    names_1 = RegexpNames()
    names_2 = ProcNames()
    assert True

names = [
    "/hello/a/b/c",
    "/hello",
    "/hello/a/c",
    "/hello/1/v/2",
    "/hello/x/v/z",
    "/world/cup",
    "/natasha/mangdor",
    "/worldcup/2018",
    "/hello/a/b",
]

def populate(handler):
    for dataname in names:
       handler.advertise("/rn-1", dataname)

def advertise_fixture(handler):
    """
    Advertise list of names using the given handler, and checks if
        the first, middle, and the last advertised name is in the advertised names.
    """
    populate(handler)
    keys = [node.dataname for node in handler.advertisements()]
    print(keys)
    return names[0] in keys and names[len(names)//2] in keys and names[-1] in keys

def test_advertise():
    assert advertise_fixture(TrieNames())
    assert advertise_fixture(RegexpNames())
    assert advertise_fixture(ProcNames())

def unadvertise_fixture(handler):
    """
    Advertise list of names using the given handler, unadvertise a name randomly,
        and checks if the unadvertised name is not in the advertised names any more.
    """
    populate(handler)
    random = names[randint(0, len(names)-1)]
    handler.unadvertise(random)
    return random not in [node.dataname for node in handler.advertisements()]

def test_unadvertise():
    assert unadvertise_fixture(TrieNames())
    assert unadvertise_fixture(RegexpNames())
    assert unadvertise_fixture(ProcNames())

def match_fixture(handler, topic, count):
    """
    Advertises list of names using the given handler, matches against a given topic,
    and compares the number of matches with the expected count.
    """
    populate(handler)
    return handler.count(topic) == count

def test_match():
    for handler in [TrieNames(), ProcNames(), RegexpNames()]:
        assert match_fixture(handler, "/hello/a/+/+", 1)
        assert match_fixture(handler, "/hello/a/#", 3)
        assert match_fixture(handler, "/hello/+/#", 5)
        assert match_fixture(handler, "/hello/#", 6)
        assert match_fixture(handler, "/nowhere/fast/+", 0)

def dump_restore_fixture(handler1, handler2):
    """
    Dumps content of a names handler to a byte array, restore it to another handler
    and check if old advertisements are still valid in the new handler.
    """
    populate(handler1)
    handler2.restore(handler1.pickle())
    return handler2.count("/hello/a/+/+") == 1 and \
           handler2.count("/hello/a/#") == 3 and \
           handler2.count("/hello/+/#") == 5 and \
           handler2.count("/hello/#") == 6 and \
           handler2.count("/nowhere/fast/+") == 0

def test_dump_restore():
    for klass1 in [TrieNames, ProcNames, RegexpNames]:
        for klass2 in [TrieNames, ProcNames, RegexpNames]:
            assert dump_restore_fixture(klass1(), klass2())

