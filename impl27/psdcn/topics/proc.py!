"""
Hard coded topic matcher for topic with MQTT-style wildcards
"""

from .table import Table

class Proc(Table):
    def __init__(self):
        super(Proc, self).__init__()

    def _do_match(self, topic, dataname):
        return do_match(topic, dataname)
# class Proc

def do_match(topic, dataname):
    match = True
    multi = False
    t_len = len(topic)
    d_len = len(dataname)
    t_pos = d_pos = 0
    while t_pos < t_len and d_pos < d_len:
        if topic[t_pos] == dataname[d_pos]:
            if d_pos == d_len-1:
                # Check for e.g. foo matching foo/#
                if t_pos == t_len-3 and topic[t_pos+1:] == "/#":
                    match = True
                    multi = True
                    break
            t_pos += 1
            d_pos += 1
            if d_pos == d_len and t_pos == t_len-1 and topic[t_pos] == '+':
                t_pos += 1
                match = True
                break
        else:
            if topic[t_pos] == '+':
                t_pos += 1
                while d_pos < d_len and dataname[d_pos] != '/':
                    d_pos += 1
                if d_pos == d_len and t_pos == t_len:
                    match = True
                    break
            elif topic[t_pos] == '#':
                multi = True
                if t_pos+1 != t_len:
                    match = False
                    break
                else:
                    match = True
                    break
            else:
                match = False
                break
    if match and d_pos == d_len and topic[t_pos:] == "/#":
        match = True
    elif not multi and (t_pos < t_len or d_pos < d_len):
        match = False
    return match

