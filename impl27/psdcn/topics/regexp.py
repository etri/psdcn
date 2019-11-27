"""
Topic matcher by rewriting into regular expressions
"""

import re as regexp
from .table import Table

class Regexp(Table):
    def __init__(self):
        super(Regexp, self).__init__()

    def _do_match(self, topic, dataname):
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

