"""
API for topics to which publications can be made
"""
class Topics(object):
    def advertise(self, dataname):
        pass

    def unadvertise(self, dataname):
        pass

    def advertisements(self):   # An iterator that yields all advertisements (dataname)
        pass

    def matches(self, topic):   # An iterator that yields all matched (dataname, content)
        pass

    def count(self):
        return len(list(self.matches("/#")))

# class Patterns
