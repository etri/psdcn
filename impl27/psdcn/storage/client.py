from gevent import socket
from .protocol import ProtocolHandler, Error
from .storage import Storage

class Client(Storage):
    def __init__(self, host='127.0.0.1', port=16170):
        super(Client, self).__init__()
        self._protocol = ProtocolHandler()
        self._channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._channel.connect((host, port))
        self._fh = self._channel.makefile('rwb')

    def _execute(self, *args):
        self._protocol.write_response(self._fh, args)
        resp = self._protocol.handle_request(self._fh)
        if isinstance(resp, Error):
            raise CommandError(resp.message)
        return resp

    def get(self, key):
        return self._execute('GET', key)

    def set(self, key, value):
        return self._execute('SET', key, value)

    def delete(self, key):
        return self._execute('DELETE', key)

    def flush(self):
        return self._execute('FLUSH')

    def mget(self, *keys):
        return self._execute('MGET', *keys)

    def mset(self, *items):
        return self._execute('MSET', *items)

