import re as regexp
from .Table import Table

class Regexp(Table):
    """
    A Table-based Names implementation which uses a matcher rewriting
        the given topic with MQTT-style wildcards using Python's re(regexp).
    """

    def __init__(self):
        super().__init__()

    def match(self, topic, dataname):
        return do_match(topic, dataname)
# class Regexp

def do_match(topic, dataname):
    if topic.find('+') == topic.find('#') == -1:
        # No wildcards, so check is simple
        return topic == dataname
    else:
        # Replace wildcards with regular expressions and match
        topic = topic.replace('#/', '(.*?/|^)').\
                replace('/#', '(/.*?|$)').\
                replace('+', '[^/#]+?')
        return regexp.compile(topic+'$').match(dataname)
