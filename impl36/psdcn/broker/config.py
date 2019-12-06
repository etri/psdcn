# Configuration 
from topics import Proc, Regexp, Trie
from storage import MemoryStorage, RedisStorage

_configs = {}

def load(file="psdcn.config"):
    with open(file) as config:
        lines = [line.strip() for line in config.readlines()]
    lines = [line for line in lines if not line.startswith("#")]
    for line in lines:
        if not '=' in line:
            continue
        eq_p = line.index('=')
        name = line[:eq_p-1].strip()
        value = line[eq_p+1:].strip()
        if not value:
            _configs[name] = True
        else:
            _configs[name] = eval(value)

def loaded():
    return _configs

def value(name, default=None):
    value = _configs.get(name, None) 
    return value if value else default
