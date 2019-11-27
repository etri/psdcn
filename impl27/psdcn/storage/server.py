# Redis-like mini server

from gevent import socket
from gevent.pool import Pool
from gevent.server import StreamServer
from socket import error as socket_error
from .protocol import ProtocolHandler
from .protocol import Error, CommandError, Disconnect
import logging
logger = logging.getLogger(__name__)

class Server(object):
    def __init__(self, host='127.0.0.1', port=16170, max_clients=128):
        self._pool = Pool(max_clients)
        self._server = StreamServer((host, port), self.connection_handler, spawn=self._pool)
        self._protocol = ProtocolHandler()
        self._kv = {}
        self._commands = self.get_commands()

    def get_commands(self):
        return {
            'get': self.get,
            'set': self.set,
            'delete': self.delete,
            'flush': self.flush,
            'mget': self.mget,
            'mset': self.mset
        }

    def connection_handler(self, conn, address):
        logger.info('Connection received: %s:%s' % address)
        # Convert "conn" (a socket object) into a file-like object.
        channel = conn.makefile('rwb')
        # Process client requests until client disconnects.
        while True:
            try:
                data = self._protocol.handle_request(channel)
                if type(data) == tuple:
                    data = list(data)
            except Disconnect:
                logger.info('Client went away: %s:%s' % address)
                break
            try:
                resp = self.run_command(data)
            except CommandError as exc:
                logger.exception('Command error')
                resp = Error(exc.args[0])
            self._protocol.write_response(channel, resp)

    def run(self):
        self._server.serve_forever()

    def run_command(self, data):
        if not isinstance(data, list):
            try:
                data = data.split()
            except:
                raise CommandError('Request must be list or simple string.')
        if not data:
            raise CommandError('Missing command')
        command = data[0].lower()
        if command not in self._commands:
            raise CommandError('Unrecognized command: %s' % command)
        else:
            logger.debug('Received %s', command)
        return self._commands[command](*data[1:])

    def get(self, key):
        return self._kv.get(key)

    def set(self, key, value):
        self._kv[key] = value
        return 1

    def delete(self, key):
        if key in self._kv:
            del self._kv[key]
            return 1
        return 0

    def flush(self):
        kvlen = len(self._kv)
        self._kv.clear()
        return kvlen

    def mget(self, *keys):
        return [self._kv.get(key) for key in keys]

    def mset(self, *items):
        data = zip(items[::2], items[1::2])
        for key, value in data:
            self._kv[key] = value
        return len(data)

def start_server():
    from gevent import monkey; monkey.patch_all()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    Server().run()

if __name__ == '__main__':
    start_server()

