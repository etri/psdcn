# Redis-like in-memory storage
# API for all complying implementations

class Storage(object):
    def __init__(self):
        pass

    def get(self, key):
        return None

    def set(self, key, value):
        return True

    def delete(self, key):
        return True

    def flush(self):
        return True

    def mget(self, *keys):
        return []

    def mset(self, *items):
        return True

