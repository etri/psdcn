"""
Hard coded topic matcher for topic with MQTT-style wildcards
"""

from .table import Table

class Proc(Table):
    def __init__(self):
        super().__init__()

    def _do_match(self, topic, dataname):
        return do_match(topic, dataname)
# class Proc

def do_match(topic, dataname):
    match = True
    multi = False
    p_len = len(topic)
    t_len = len(dataname)
    p_pos = t_pos = 0
    while p_pos < p_len and t_pos < t_len:
        if topic[p_pos] == dataname[t_pos]:
            if t_pos == t_len-1:
                # Check for e.g. foo matching foo/#
                if p_pos == p_len-3 and topic[p_pos+1:] == "/#":
                    match = True
                    multi = True
                    break
            p_pos += 1
            t_pos += 1
            if t_pos == t_len and p_pos == p_len-1 and topic[p_pos] == '+':
                p_pos += 1
                match = True
                break
        else:
            if topic[p_pos] == '+':
                p_pos += 1
                while t_pos < t_len and dataname[t_pos] != '/':
                    t_pos += 1
                if t_pos == t_len and p_pos == p_len:
                    match = True
                    break
            elif topic[p_pos] == '#':
                multi = True
                if p_pos+1 != p_len:
                    match = False
                    break
                else:
                    match = True
                    break
            else:
                match = False
                break
    if match and t_pos == t_len and topic[p_pos:] == "/#":
        match = True
    elif not multi and (p_pos < p_len or t_pos < t_len):
        match = False
    return match

