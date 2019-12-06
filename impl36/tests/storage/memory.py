import sys
sys.path.append("../../psdcn")
from storage import MemoryStorage
from tester import test

test(MemoryStorage())

