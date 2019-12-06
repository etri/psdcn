class Slot(object):
    def __init__(self, dataname, rn_name):
        self.dataname = dataname
        self.rn_name = rn_name

    @property
    def dataname(self):
        return self._dataname

    @property
    def rn_name(self):
        return self._rn_name

    @dataname.setter
    def dataname(self, dataname):
        self._dataname = dataname

    @rn_name.setter
    def rn_name(self, rn_name):
        self._rn_name = rn_name
