# Hash the first prefix of the given name
# and suggest the broker according to the computed hash value

"""
def arbit(name, brokers):
    prefix = name.split("/")[1]
    h = abs(sum([ord(char) for char in prefix])) % len(brokers)
    return brokers[h]
"""
import siphash

def arbit(name, brokers):
    key = b'0123456789ABCDEF'
    prefix = name.split("/")[1].encode()
    h = abs(siphash.SipHash_2_4(key, prefix).hash()) % len(brokers)
    return brokers[h]
