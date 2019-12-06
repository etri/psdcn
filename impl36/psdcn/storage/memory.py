# Redis-like in-memory storage

from .storage import Storage

class Memory(Storage):
    def __init__(self):
        super().__init__()
        self._storage = {}

    def get(self, key):
        if key in self._storage:
            return self._storage[key]
        return None

    def set(self, key, value):
        self._storage[key] = value
        return 1

    def delete(self, key):
        if key in self._storage:
            del self._storage[key]
            return 1
        return 0

    def flush(self):
        self._storage.clear()
        return 1

    def mget(self, *keys):
        return [self._storage.get(key) for key in keys]

    def mset(self, *items):
        data = list(zip(items[::2], items[1::2]))
        for key, value in data:
            self._storage[key] = value
        return len(data)

