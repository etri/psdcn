# Pub/Sub operations database

import pickle

class PSO(object):
    def __init__(self):
        self.pubadvs = {}

    def __str__(self):
        return f"psodb: {self.pubadvs}"

    def pubadv(self, dataname, pubadvinfo):
        self.pubadvs[dataname] = pubadvinfo

    def __contains__(self, dataname):
        return dataname in self.pubadvs

    def __getitem__(self, dataname):
        if dataname in self:
            return self.pubadvs[dataname]
        return None

    def pubunadv(self, dataname):
        if dataname in self.pubadvs:
            del self.pubadvs[dataname]

    def count(self):
        return len(self.pubadvs)

    def advertisements(self):
        yield from self.pubadvs.items()

    def names(self):
        for dataname, pubadvinfo in self.advertisements():
            yield dataname

    def pickle(self):
        return pickle.dumps(list(self.advertisements()))

    def restore(self, pickled):
        records = pickle.loads(pickled)
        for dataname, pubadvinfo in records:
            self.pubadv(dataname, pubadvinfo)
