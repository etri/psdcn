import sys
sys.path.append("../../../psdcnv2")
sys.path.append("../../..")
from time import time
from store import Store, TableStorage, RedisStorage, FileStorage, CacheWrapper
import redis

def test_read(provider, storage, count=100000):
    store = Store(storage)
    start = time()
    HSKIM = 1800
    NATASHA = 1870
    TUPLE = ('psdcn', 2, 'big big success')
    store.set('hskim', HSKIM)
    store.set('natasha', NATASHA)
    store.set('tuple', TUPLE)
    for run in range(count):
        _hskim = int(store.get('hskim'))
        _natasha = int(store.get('natasha'))
        _tuple = eval(store.get('tuple'))
    end = time()
    print(provider, "took", format("%.2f" % (end - start)))
    store.clear()
    
def test_store(provider, storage, count=100000):
    store = Store(storage)
    start = time()
    for run in range(count):
        KEY = 'hskim_' + str(run)
        store.set(KEY, run)
        _value = store.get(KEY)
    end = time()
    print(provider, "took", format("%.2f" % (end - start)))
    store.clear()
    
def test_test(_storage, cache_size):
    print("Cache size:", cache_size)
    print()
    print("READ Tests")
    for provider, storage in _storage.items():
        test_read(provider, storage)
    print()
    print("WRITE Tests")
    for provider, storage in _storage.items():
        test_store(provider, storage)
    print("\n")

def main():
    fileStorage = FileStorage()
    fileStorage.root = "test.dir"
    normal_storage = {
        "TableStorage": TableStorage(),
        "FileStorage": fileStorage,
        "RedisStorage": RedisStorage(redis.StrictRedis()),
    }
    test_test(normal_storage, 0)
    for cache_size in [1, 10000, 100000, 500000, 1000000]:
        cached_storage = { provider: CacheWrapper(storage, cache_size)
                            for provider, storage in normal_storage.items() }
        test_test(cached_storage, cache_size)

if __name__ == "__main__":
    main()

