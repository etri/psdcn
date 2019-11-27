from io import BytesIO
from collections import namedtuple

Error = namedtuple('Error', ('message',))

class CommandError(Exception): pass
class Disconnect(Exception): pass

class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            '+': self.handle_simple_string,
            '-': self.handle_error,
            ':': self.handle_integer,
            '!': self.handle_float,
            '$': self.handle_string,
            '*': self.handle_list,
            '&': self.handle_tuple,
            '%': self.handle_dict
        }

    def handle_request(self, channel):
        first_byte = channel.read(1)
        if not first_byte:
            raise Disconnect()
        try:
            # Delegate to the appropriate handler based on the first byte.
            return self.handlers[first_byte](channel)
        except KeyError:
            raise CommandError('bad request')

    def handle_simple_string(self, channel):
        return channel.readline().rstrip('\r\n')

    def handle_error(self, channel):
        return Error(channel.readline().rstrip('\r\n'))

    def handle_integer(self, channel):
        return int(channel.readline().rstrip('\r\n'))

    def handle_float(self, channel):
        return float(channel.readline().rstrip('\r\n'))

    def handle_string(self, channel):
        # First read the length ($<length>\r\n).
        length = int(channel.readline().rstrip('\r\n'))
        if length == -1:
            return None  # Special-case for NULLs.
        length += 2  # Include the trailing \r\n in count.
        return channel.read(length)[:-2]

    def handle_list(self, channel):
        num_elements = int(channel.readline().rstrip('\r\n'))
        return [self.handle_request(channel) for _ in range(num_elements)]
    
    def handle_tuple(self, channel):
        return tuple(self.handle_list(channel))

    def handle_dict(self, channel):
        num_items = int(channel.readline().rstrip('\r\n'))
        elements = [self.handle_request(channel)
                    for _ in range(num_items * 2)]
        return dict(zip(elements[::2], elements[1::2]))

    def write_response(self, channel, data):
        buf = BytesIO()
        self._write(buf, data)
        buf.seek(0)
        channel.write(buf.getvalue())
        channel.flush()

    def _write(self, buf, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(data, bytes):
            buf.write('$%s\r\n%s\r\n' % (len(data), data))
        elif isinstance(data, int):
            buf.write(':%s\r\n' % data)
        elif isinstance(data, float):
            buf.write('!%s\r\n' % data)
        elif isinstance(data, Error):
            buf.write('-%s\r\n' % error.message)
        elif isinstance(data, list):
            buf.write('*%s\r\n' % len(data))
            for item in data:
                self._write(buf, item)
        elif isinstance(data, tuple):
            buf.write('&%s\r\n' % len(data))
            for item in data:
                self._write(buf, item)
        elif isinstance(data, dict):
            buf.write('%%%s\r\n' % len(data))
            for key in data:
                self._write(buf, key)
                self._write(buf, data[key])
        elif data is None:
            buf.write('$-1\r\n')
        else:
            raise CommandError('unrecognized type: %s' % type(data))

def idempotent(data):
    proto = ProtocolHandler()
    buf = BytesIO()
    proto._write(buf, data)
    buf.seek(0)
    print 'Given:', data, 'EncDec:', proto.handle_request(buf)

if __name__ == "__main__":
    for data in [100, "Hello", 3.14159, (1.414, 2), [1.414, 2],
            {'name': ('Gil Dong', 'Hong'), 'grad-years': [1980, 1984, 1986]}]:
        idempotent(data)

