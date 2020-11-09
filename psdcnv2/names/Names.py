import logging
import pickle

class Names(object):
    """
    Collection of data names to which puplications can be made.
    """

    def __init__(self):
        pass

    def advertise(self, rn_name, dataname):
        """
        Advertise a data name `dataname` informing that publications will be made
            at the specific RN `rn_name`.

        :param rn_name: RN name where the actual data will be published
        :type rn_name: str
        :param dataname: a data name to which publications will be made
        :type rn_name: str
        """
        pass

    def unadvertise(self, dataname):
        """
        The name `dataname` will be removed from the collection of legitimate names
            to which publications can be made. 

        :param dataname: a data name to which publications will be made
        :type rn_name: str
        """
        pass

    def advertisements(self):
        """
        A generator iterators that yield all advertisements (rn_name, dataname).
        """
        yield from self.matches("/#")

    def names(self):
        """
        A generator iterators that yield all datanames advertised so far.
        """
        for slot in self.advertisements():
            yield slot.dataname

    def matches(self, topic):
        """
        An iterator that yields all matches  for the given `topic`.
        """
        return False

    def __contains__(self, dataname):
        """
        Checks if the given `dataname` is contained in the collection of data names.

        :param dataname: a data name to which publications will be made
        :type rn_name: str
        """
        return False

    def __getitem__(self, dataname):
        for match in self.matches(dataname):
            return match
        return None

    def count(self, topic="/#"):
        """
        Returns the number of advertised data names.

        :return: number of advertised data names.
        :rtype: int
        """
        return sum(1 for _ in self.matches(topic))

    def pickle(self):
        """
        Collects advertisements made so far into a byte array which can be restored later.

        :return: a byte array representation of all the advertisements
        :rtype: byte[]
        """
        return pickle.dumps([(slot.rn_name, slot.dataname) for slot in self.advertisements()])

    def restore(self, pickled):
        """
        Restores advertisements from a pickled representation made earlier.

        :param: a byte array representation of advertisements
        :type: byte[]
        """
        records = pickle.loads(pickled)
        for rn_name, dataname in records:
            self.advertise(rn_name, dataname)

    def set_context(self, context):
        pass
