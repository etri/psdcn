import sys
sys.path.append("..")
from io import BytesIO
from storage import ProtocolHandler

_OK = {'Status': 'OK' }
_Error = {'Status': 'Error'}

class PubsubService(object):
    def __init__(self, topics, storage):
        # Implementations for dataname and storage handlers
        # will be determined by configuration data
        self._server = self
        self._names = topics
        self._storage = storage

    # Generic handler with dynamic dispatch based-on proto name
    def handle(self, command, *params):
        parts = command.split("/")[1:]
        rn_name = parts[0]
        proto = 'handle_' + parts[1]
        name = "/" + ('/'.join(parts[2:]))
        return getattr(self, proto)(name, rn_name, *params) # THE MAGIC!

    # Handlers
    # All handlers take this form:
    #   handle_command(self, command, name[dataname or topic], rn_name, ...)
    # A handler can take additional parameters from the ... part

    def handle_pubadv(self, name, rn_name, *params):
        self._names.advertise(name, rn_name, *params)
        self._storage.set(name, [])
        return _OK

    def handle_pubunadv(self, name, rn_name, *params):
        self._names.unadvertise(name, *params)  # rn_name ignored
        self._storage.delete(name)
        return _OK

    def handle_pubdata(self, name, rn_name, *params):
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
    
    def handle_subtopic(self, name, rn_name, *params):
        # This operation needs not be handled by the broker
        # since subscription information is maintained by the clients instead.
        # The following code is just for tests
        sub_names = ["/" + node.rn_name + node.dataname for node in self._names.matches(name)]
        # print(sub_names)
        return _OK

    def handle_manitopic(self, name, rn_name, *params):
        return [node.dataname for node in self._names.matches(name)]

    def handle_manidata(self, name, rn_name, *params):
        return len(self._storage.get(name))

    def handle_subdata(self, name, rn_name, *params):
        # Assume here that the sequence number to fetch published data from
        # that position is at params[0]
        logged_data = self._storage.get(name)
        index_from = int(params[0])-1
        return logged_data[index_from:]

    # *-- Added per ETRI's request on Nov. 5th --*
    def handle_listnames(self, name, rn_name, *params):
        # Return coded buffer of datanames advised so far
        # encoded using the ProtocolHandler's wire encoding mechanism
        # which can be decoded by proto.handle_request(coded)
        proto = ProtocolHandler()
        coded = BytesIO()
        proto._write(coded, list(self._names.advertisements()))
        coded.seek(0)
        return coded

