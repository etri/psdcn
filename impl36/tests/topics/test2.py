import sys
sys.path.append("../../psdcn")
from time import time
from topics import Trie, Proc, Regexp

def init(publication):
    for i in range(500):
        publication.advertise("/etri/bldg7/room318/" + str(i), "rn1")
    for i in range(500):
        publication.advertise("/etri/bldg310/room628/" + str(i), "rn1")

def test_matches(publication, verbose=True):
    for match in publication.matches("/etri/bldg7/room318/+"):
        pass

if __name__ == "__main__":
    if len(sys.argv) == 1:
        algorithm = "trie"
    else:
        algorithm = sys.argv[1]
    algorithm = algorithm.capitalize()
    print("Using", algorithm)
    exec("from topics import " + algorithm, globals())
    publisher = eval(algorithm + "()")
    init(publisher)
    print("Done advertising. # of datanames is", publisher.count())
    start = time()
    algorithm += "()"
    for i in range(1000):
        test_matches(publisher, verbose=False)
    end = time()
    print("Elapsed time:", (end-start), "seconds")

