import sys
sys.path.append("../../psdcn")
from time import time
from topics import Trie, Proc, Regexp

def test_matches(publication, verbose=True):
    publication.advertise("/hello", "rn1")
    publication.advertise("/hello/a/b/c", "rn1")
    publication.advertise("/hello/d", "rn2")
    publication.unadvertise("/hello")
    for match in publication.matches("/hello/+/#"):
        pass
    for match in publication.matches("/hello/a/+/+"):
        pass
    for match in publication.matches("/hello/#"):
        pass

if __name__ == "__main__":
    if len(sys.argv) == 1:
        algorithm = "trie"
    else:
        algorithm = sys.argv[1]
    algorithm = algorithm.capitalize()
    print "Using", algorithm
    exec("from topics import " + algorithm, globals())
    start = time()
    algorithm += "()"
    for i in range(100000):
        test_matches(eval(algorithm), verbose=False)
    end = time()
    print "Elapsed time:", (end-start), "seconds"

