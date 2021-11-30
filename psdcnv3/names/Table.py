from .Names import Names
from .Slot import Slot

class Table(Names):
    """
    A Names implementation which uses Dict Table as the main data structure.
    """
    def __init__(self):
        super().__init__()
        self._datanames = {}

    def __contains__(self, dataname):
        return dataname in self._datanames

    def count(self):
        return len(self._datanames)

    def advertise(self, rn_name, dataname, pub_moved=False):
        if not pub_moved:
            rn_names = [rn_name]
        else:
            rn_names = self._datanames[dataname].rn_names + [rn_name]
        self._datanames[dataname] = Slot(rn_names, dataname)

    def unadvertise(self, dataname):
        if dataname in self._datanames:
            del self._datanames[dataname]

    def matches(self, topic):
        for dataname in self._datanames:
            if self.match(topic, dataname):
                yield self._datanames[dataname]

    def match(self, topic, dataname):               # Define it at subclasses!
        pass
