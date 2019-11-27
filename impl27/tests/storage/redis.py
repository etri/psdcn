import sys
sys.path.append("../../psdcn")
from storage import RedisStorage
from tester import test

test(RedisStorage())

