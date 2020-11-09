from .Storage import Storage
from psdcnv2.utils import build_path
import os, pickle

class TableStorage(Storage):
    """
    An in-memory dict-based implementation of `Storage`.
    """
    def __init__(self):
        self.table = {}

    def __str__(self):
        return "#{TableStorage with %d elts}"%(len(self.keys()))

    def __contains__(self, key):
        return key in self.table

    def media(self):
        return f"TableStorage"

    def set_context(self, context):
        self.rnname = context.id
        self.logger = context.logger
        self.path = "dump" + build_path(self.rnname) + ".table"

    def get(self, key):
        return self.table[key] if key in self.table else None

    def set(self, key, value):
        self.table[key] = value

    def delete(self, key):
        if key in self.table:
            del self.table[key]

    def keys(self):
        return list(self.table.keys())

    def clear(self):
        self.table.clear()

    def flush(self):
        with open(self.path, "wb") as f:
            f.write(pickle.dumps(self.table))
            f.flush()

    def restore(self):
        if not os.path.isfile(self.path):
            self.logger.debug(f"Table data for {self.rnname} not found")
        try:
            with open(self.path, "rb") as f:
                self.table = pickle.loads(f.read())
        except Exception:
            self.logger.debug(f"Table data restoration failed for {self.rnname}")

