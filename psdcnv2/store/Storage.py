class Storage(object):
    """
    Common protocol for the Storage provider which provides actual data management
        services to the surrounding `Store`.

    Storage is not indexed, and thus write to a key with a value completely replaces
        any previous value if any is present.
    """
    def __init__(self):
        pass

    def __str__(self):
        """
        External name for the storage.
        Defaults to a string with the number of elements information.
        """
        return "#{Storage with %d elts}"%(len(self.keys()))

    def __contains__(self, key):
        """
        Checks if the given `key` is a legitimate name for which data were written.
        """
        return False

    def media(self):
        return "Storage"

    def set_context(self, context):
        self.context = context

    def get(self, key):
        """
        Returns the value corresponding to the `key`. Returns None if no value
            corresponding to `key` exists.
        """
        return None

    def mget(self, keys):
        """
        Gathers values corresponding to the `keys`.
        """
        return [self.get(key) for key in keys]

    def set(self, key, value):
        """
        Writes the `value` under the name `key`.
        """
        pass

    def mset(self, kvs):
        """
        Writes (key, value) of `kvs` in bulk mode.
        """
        for key, value in kvs.items():
            self.set(key, value)

    def delete(self, key):
        """
        Removes the `key` and invalidates all further read/write requests to it.
        """
        pass

    def keys(self):
        """
        Returns list of data names maintained in the storage.
        """
        return []

    def flush(self):
        """
        Writes out all the deferred or delayed write data to the actual storage.
        """
        pass

    def restore(self):
        """
        Restores data that has been written out
        """
        pass

    def clear(self):
        """
        Removes all data names from the storage.
        """
        for key in self.keys():
            self.delete(key)
