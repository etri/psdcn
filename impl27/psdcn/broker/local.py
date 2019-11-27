from .service import PubsubService
from .config import load as load_config, value as config_value
from topics import Trie
from storage import MemoryStorage

class LocalServer(PubsubService):
    def __init__(self, topics, storage):
        super(LocalServer, self).__init__(topics, storage)

    def __str__(self):
        return "#{LocalServer topics=" + self._names.__class__.__name__ + \
                           ", storage=" + self._storage.__class__.__name__ + "}"

def localserver(*argv):
    load_config(*argv)
    topics = config_value("topics", Trie())
    storage = config_value("storage", MemoryStorage())
    return LocalServer(topics, storage)

