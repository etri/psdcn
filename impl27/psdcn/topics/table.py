"""
Table-based topic management
"""

from .topics import Topics
from .slot import Slot

class Table(Topics):
    def __init__(self):
        self._datanames = {}

    def advertise(self, dataname, rn_name):
        self._datanames[dataname] = rn_name

    def unadvertise(self, dataname):
        if dataname in self._datanames:
            del self._datanames[dataname]

    def advertisements(self):
        for dataname in self._datanames.items():
            yield dataname

    def matches(self, topic):
        for dataname in self._datanames:
            if self._do_match(topic, dataname):
                yield Slot(dataname, self._datanames[dataname])

    def _do_match(self, topic, dataname):          # Define it at subclasses!
        pass
# class Table
