from .Storage import Storage

class RedisStorage(Storage):
    """
    An implementation of `Storage` which uses Redis-server as the actual storage.
    """

    def __init__(self, redis):
        """
        :param redis: a Redis-server proxy (recommend redis.StrictRedis instance).
        """
        # assert redis is not None
        self.redis = redis

    def __str__(self):
        return "#{RedisStorage with %d elts}"%len(self.keys())

    def __contains__(self, key):
        return self.redis.exists(key)

    def media(self):
        return f"RedisStorage"

    def get(self, key):
        return self.redis.get(key)

    def mget(self, keys):
        return self.redis.mget(keys)

    def set(self, key, value):
        self.redis.set(key, value)      # Ignore TTL issues until it is required

    def mset(self, kvs):
        self.redis.mset(kvs)            # Redis has cheaper way of doing bulk write

    def delete(self, key):
        self.redis.delete(key)

    def keys(self):
        return list(map(lambda b: b.decode(), self.redis.keys(pattern='*')))

    def flush(self):
        self.redis.bgsave()

    def clear(self):
        self.redis.flushdb()

