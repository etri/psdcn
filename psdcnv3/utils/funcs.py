import json
import siphash

def arbit(name, choices):
    key = b'0123456789ABCDEF'
    prefix = name.split("/")[1].encode()
    h = abs(siphash.SipHash_2_4(key, prefix).hash()) % len(choices)
    # print(f"ARBIT chose {choices[h]} from {choices} for dataname {name}")
    return choices[h]

def param_value(params, param_type, value_type):
    try:
        return params[param_type][value_type]
    except:
        return None

def build_path(name):
    return "." + ''.join([c for c in name if c.isalnum()])

