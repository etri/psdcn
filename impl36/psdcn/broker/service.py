import sys
sys.path.append("..")

_OK = {'Status': 'OK' }
_Error = {'Status': 'Error'}

class PubsubService(object):
    def __init__(self, topics, storage):
        # Implementations for dataname and storage handlers
        # will be determined by configuration data
        self._server = self
        self._datanames = topics
        self._storage = storage
        self.handlers = {
            "pubadv": self.handlePubAdv,
            "pubunadv": self.handlePubUnadv,
            "pubdata": self.handlePubData,
            "manitopic": self.handleManiTopic,
            "manidata": self.handleManiData,
            "subdata": self.handleSubData,
        }

    # Generic handler
    def handle(self, command, *params):
        parts = command.split("/")[1:]
        rn_name = parts[0]
        proto = parts[1]
        name = "/" + ('/'.join(parts[2:]))
        if proto in self.handlers:
            return self.handlers[proto](name, rn_name, *params)

    # Handlers
    # All handlers take this form:
    #   handleCommandX(self, command, name[dataname or topic], rn_name, ...)
    # A handler can take additional parameters from the ... part

    def handlePubAdv(self, name, rn_name, *params):
        self._datanames.advertise(name, rn_name, *params)
        self._storage.set(name, [])
        return _OK

    def handlePubUnadv(self, name, rn_name, *params):
        self._datanames.unadvertise(name, *params)  # rn_name ignored
        self._storage.delete(name)
        return _OK

    def handlePubData(self, name, rn_name, *params):
        # Look into params if this request is a SHORT or LONG publish request.
        # Assume data to publish is the first element of params for SHORT publish.
        last_sep = name.rindex("/")
        seq_no = name[last_sep+1:]
        try:
            seq_no = int(seq_no)
        except:
            return _Error
        name = name[:last_sep]
        old_data = self._storage.get(name)  
        if old_data == None:
            return _Error
        old_len = len(old_data)
        if old_len < seq_no:
            for _ in range(seq_no - old_len):
                old_data = old_data + [None]
        old_data[seq_no-1] = params[0]
        self._storage.set(name, old_data)
        return _OK
    
    def handleSubTopic(self, name, rn_name, *params):
        # This operation needs not be handled by the broker
        # since subscription information is maintained by the clients instead.
        # The following code is just for tests
        sub_names = ["/" + node.rn_name + node.dataname for node in self._datanames.matches(name)]
        # print(sub_names)
        return _OK

    def handleManiTopic(self, name, rn_name, *params):
        return [node.dataname for node in self._datanames.matches(name)]

    def handleManiData(self, name, rn_name, *params):
        return len(self._storage.get(name))

    def handleSubData(self, name, rn_name, *params):
        # Assume here that the sequence number to fetch published data from
        # that position is at params[0]
        logged_data = self._storage.get(name)
        index_from = int(params[0])-1
        return logged_data[index_from:]

