from .Names import Names
from .Slot import Slot

class Trie(Names):
    """
    A Names implementation which uses Trie as the main data structure.
    """

    # Trie nodes
    class Node(Slot):
        def __init__(self, rn_name, dataname):
            super().__init__(rn_name, dataname)
            self.children = {}

    # Trie methods
    def __init__(self):
        super().__init__()
        self._root = self.Node(None, None)

    def __contains__(self, dataname):
        for _ in self.matches(dataname):
            return True
        return False

    def locate(self, dataname):
        node = self._root
        for part in dataname.split('/'):
            node = node.children.setdefault(part, self.Node(None, None))
        return node;

    def advertise(self, rn_name, dataname):
        node = self.locate(dataname)
        node.rn_name = rn_name
        node.dataname = dataname

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

    def matches(self, topic):
        parts = topic.split('/')
        def match(node, i=0):
            if i == len(parts):
                if node.dataname and node.rn_name:
                    yield node
            else:
                part = parts[i]
                if part in node.children:
                    yield from match(node.children[part], i + 1)
                if part == '+':
                    for child in node.children:
                        yield from match(node.children[child], i + 1)
                if part == '#':
                    yield from match(node, i + 1)
                    for child in node.children:
                        yield from match(node.children[child], i)
        yield from match(self._root)
