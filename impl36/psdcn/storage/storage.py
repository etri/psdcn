# Redis-like in-memory storage
# API for all complying implementations

class Storage(object):
    def __init__(self):
        pass

    def _execute(self, *args):
        return 0

    def get(self, key):
        return None

    def set(self, key, value):
        return 1

    def delete(self, key):
        return 1

    def flush(self):
        return 1

    def mget(self, *keys):
        return []

    def mset(self, *items):
        return 0

