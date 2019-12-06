from io import BytesIO
from collections import namedtuple

Error = namedtuple('Error', ('message',))

class CommandError(Exception): pass
class Disconnect(Exception): pass

class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            b'+': self.handle_simple_string,
            b'-': self.handle_error,
            b':': self.handle_integer,
            b'!': self.handle_float,
            b'$': self.handle_string,
            b'*': self.handle_list,
            b'&': self.handle_tuple,
            b'%': self.handle_dict}

    def handle_request(self, channel):
        first_byte = channel.read(1)
        if not first_byte:
            raise Disconnect()
        try:
            # Delegate to the appropriate handler based on the first byte.
            return self.handlers[first_byte](channel)
        except KeyError:
            raise CommandError('Bad request')

    def handle_simple_string(self, channel):
        line = channel.readline().decode()
        return line.rstrip('\r\n')

    def handle_error(self, channel):
        line = channel.readline().decode()
        return Error(line.rstrip('\r\n'))

    def handle_integer(self, channel):
        line = channel.readline().decode()
        return int(line.rstrip('\r\n'))

    def handle_float(self, channel):
        line = channel.readline().decode()
        return float(line.rstrip('\r\n'))

    def handle_string(self, channel):
        # First read the length ($<length>\r\n).
        line = channel.readline().decode()
        length = int(line.rstrip('\r\n'))
        if length == -1:
            return None  # Special-case for NULLs.
        length += 2  # Include the trailing \r\n in count.
        data = channel.read(length).decode()
        return data[:-2]

    def handle_list(self, channel):
        line = channel.readline().decode()
        num_elements = int(line.rstrip('\r\n'))
        return [self.handle_request(channel) for _ in range(num_elements)]
    
    def handle_tuple(self, channel):
        return tuple(self.handle_list(channel))

    def handle_dict(self, channel):
        line = channel.readline().decode()
        num_items = int(line.rstrip('\r\n'))
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
            data = '$%s\r\n%s\r\n' % (len(data), str(data))
            buf.write(data.encode())
        elif isinstance(data, int):
            data = ':%s\r\n' % data
            buf.write(data.encode())
        elif isinstance(data, float):
            data = '!%s\r\n' % data
            buf.write(data.encode())
        elif isinstance(data, Error):
            buf.write(('-%s\r\n' % error.message).encode())
        elif isinstance(data, list):
            slen = '*%s\r\n' % len(data)
            buf.write(slen.encode())
            for item in data:
                self._write(buf, item)
        elif isinstance(data, tuple):
            slen = '&%s\r\n' % len(data)
            buf.write(slen.encode())
            for item in data:
                self._write(buf, item)
        elif isinstance(data, dict):
            slen = '%%%s\r\n' % len(data)
            buf.write(slen.encode())
            for key in data:
                self._write(buf, key)
                self._write(buf, data[key])
        elif data is None:
            buf.write(('$-1\r\n').encode())
        else:
            raise CommandError('Unrecognized type: %s' % type(data))

def idempotent(data):
    proto = ProtocolHandler()
    buf = BytesIO()
    proto._write(buf, data)
    buf.seek(0)
    print('Given:', data, 'EncDec:', proto.handle_request(buf))

if __name__ == "__main__":
    for data in [100, "Hello", 3.14159, (1.414, 2), [1.414, 2],
            {'name': ('Gil Dong', 'Hong'), 'grad-years': [1988, 1992, 1996]}]:
        idempotent(data)

