"""
Topic matcher that uses a trie to store values associated with filters
"""

from .topics import Topics
from .slot import Slot

# Trie nodes
class Node(Slot):
    def __init__(self):
        super(Node, self).__init__(None, [])
        self.children = {}
        self.dataname = None
        self.metadata = None

class Trie(Topics):

    # Trie methods
    def __init__(self):
        self._root = Node()

    def advertise(self, dataname, rn_name):
        node = self._root
        for part in dataname.split('/'):
            node = node.children.setdefault(part, Node())
        node.dataname = dataname
        node.rn_name = rn_name

    def unadvertise(self, dataname):
        parts = []
        try:
            parent, node = None, self._root
            for part in dataname.split('/'):
                parent, node = node, node.children[part]
                parts.append((parent, part, node))
            if node.rn_name:
                node.rn_name = None
            if node.dataname:
                node.dataname = None
        except KeyError:
            # raise KeyError(dataname)
            pass
        else:   # cleanup
            for parent, part, node in reversed(parts):
                if node.children or node.rn_name:
                    break
                del parent.children[part]

    def advertisements(self):
        for match in self.matches("/#"):
            yield match.dataname, match.rn_name

    def matches(self, topic):
        parts = topic.split('/')
        def do_match(node, i=0):
            if i == len(parts):
                if node.dataname and node.rn_name:
                    yield node
            else:
                part = parts[i]
                if part in node.children:
                    for match in do_match(node.children[part], i + 1):
                        yield match
                if part == '+':
                    for child in node.children:
                        for match in do_match(node.children[child], i + 1):
                            yield match
                if part == '#':
                    for match in do_match(node, i + 1):
                        yield match
                    for child in node.children:
                        for match in do_match(node.children[child], i):
                            yield match
        for match in do_match(self._root):
            yield match

# class Trie
