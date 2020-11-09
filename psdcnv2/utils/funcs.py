# Miscellaneous functions

def param_value(params, param_type, value_type):
    try:
        return params[param_type][value_type]
    except:
        return None

def build_path(name):
    return "." + ''.join([c for c in name if c.isalnum()])

