import sys
sys.path.append("../../../psdcnv2")
from time import time
from names import TrieNames, ProcNames, RegexpNames

def init(handler):
    for i in range(500):
        handler.advertise("rn1", "/etri/bldg7/room318/" + str(i))
    for i in range(500):
        handler.advertise("rn1", "/etri/bldg310/room628/" + str(i))

def test_matches(handler, verbose=True):
    for node in handler.matches("/etri/+"):
        pass

if __name__ == "__main__":
    if len(sys.argv) == 1:
        algorithm = "trie"
    else:
        algorithm = sys.argv[1]
    algorithm = algorithm.capitalize() + "Names"
    print("Using", algorithm)
    exec("from names import " + algorithm, globals())
    publisher = eval(algorithm + "()")
    init(publisher)
    print("Done advertising. # of datanames is", publisher.count())
    start = time()
    algorithm += "()"
    for i in range(1000):
        test_matches(publisher, verbose=False)
    end = time()
    print("Elapsed time:", (end-start), "seconds")
