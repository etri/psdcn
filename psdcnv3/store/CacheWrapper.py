from .Storage import Storage
import logging

class CacheWrapper(Storage):
    """
    A `Storage` wrapper for LRU cache based-on Python dict.
    Can wrap any PSDCNv3 `Storage` and convert it to a cached one.

    Python 3.6 completely revamped dictionary implementation to use linked hashmap,
        Dicts are now ordered by insertion-order.
        We can exploit this to use the dict as a LRU cache in O(1) time qute easily.
    """

    def __init__(self, inner, capacity):
        """
        :param inner: a `Storage` to which the cache functionality will be added.
        :type inner: `Storage`-conformant provider
        :param capacity: size (number of data items) of the cache
        """
        assert capacity > 0
        self.inner = inner
        self.capacity = capacity
        self._lru = {}

    def __str__(self):
        return "#{Cache with %d elts over %s}"%(len(self._lru), str(self.inner))

    def __contains__(self, key):
        return key in self._lru or key in self.inner

    def media(self):
        return f"Cache of {self.capacity} items over {self.inner.media()}"

    def set_context(self, context):
        self.inner.set_context(context)

    def get(self, key):
        if key in self._lru:
            value = self._lru[key]
            del self._lru[key]
        else:
            try:
                value = self.inner.get(key)
                if value is None:
                    return value
            except:
                return None
        # Reset ordering by re-inserting the key in the dict
        self._lru[key] = value
        return value

    def set(self, key, value):
        # If key already exists, update the value
        if key in self._lru:
            del self._lru[key]
        # Else, remove the oldest key exploiting Python's dict ordering
        elif len(self._lru) == self.capacity:
            for out in self._lru:
                write = self._lru[out]
                self.inner.set(out, write)
                del self._lru[out]
                break
        self._lru[key] = value

    def delete(self, key):
        if key in self._lru:
            del self._lru[key]
        if key in self.inner:
            self.inner.delete(key)

    def flush(self):
        self.inner.mset(self._lru)
        self.inner.flush()

    def restore(self):
        self.inner.restore()

    def clear(self):
        self.inner.clear()
        self._lru.clear()

    def keys(self):
        return set(list(self._lru.keys()) + list(self.inner.keys()))
