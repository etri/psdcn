import sys
sys.path.append("../../../psdcnv2")
from time import time
from names import TrieNames, ProcNames, RegexpNames

def test_matches(handler, verbose=True):
    handler.advertise("rn1", "/hello")
    handler.advertise("rn1", "/hello/a/b/c")
    handler.advertise("rn2", "/hello/d")
    handler.unadvertise("/hello")
    for match in handler.matches("/hello/+/#"):
        pass
    for match in handler.matches("/hello/a/+/+"):
        pass
    for match in handler.matches("/hello/#"):
        pass

if __name__ == "__main__":
    if len(sys.argv) == 1:
        algorithm = "trie"
    else:
        algorithm = sys.argv[1]
    algorithm = algorithm.capitalize() + "Names"
    print("Using", algorithm)
    exec("from names import " + algorithm, globals())
    start = time()
    algorithm += "()"
    for i in range(100000):
        test_matches(eval(algorithm), verbose=False)
    end = time()
    print("Elapsed time:", (end-start), "seconds")
