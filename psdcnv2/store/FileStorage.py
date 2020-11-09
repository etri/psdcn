import os, os.path
import shutil
from io import BytesIO
from .Storage import Storage
from psdcnv2.utils import build_path

class FileStorage(Storage):
    """
    An implementation of `Storage` based-on the file system of the underlying system.
    Adapted from the `simplekv` package and made conform to `Storage` interface.
    """

    def __init__(self):
        self.bufsize = 1024*1024    # 1m

    def __str__(self):
        return "#{FileStorage with %d elts}"%len(self.keys())

    def __contains__(self, key):
        return os.path.exists(self.path_name(key))

    def media(self):
        return f"FileStorage of bufsize {self.bufsize}"

    def set_context(self, context):
        self.root = "dump" + build_path(context.id) + ".dir"

    def get(self, key):
        file = BytesIO()
        try:
            source = self.open(key)
            try:
                bufsize = self.bufsize
                while True:
                    buf = source.read(bufsize)
                    file.write(buf)
                    if len(buf) < bufsize:
                        break
                return file.getvalue()
            finally:
                source.close()
        except KeyError:
            return None

    def set(self, key, value):
        value = BytesIO(value)
        bufsize = self.bufsize
        target = self.path_name(key)
        self.mkdir(os.path.dirname(target))
        with open(target, 'wb') as f:
            while True:
                buf = value.read(bufsize)
                f.write(buf)
                if len(buf) < bufsize:
                    break

    def delete(self, key):
        try:
            targetname = self.path_name(key)
            os.unlink(targetname)
            self.remove_empty_parents(targetname)
        except OSError as e:
            if not e.errno == 2:
                raise

    def keys(self):
        root = os.path.abspath(self.root)
        result = []
        for dp, dn, fn in os.walk(root):
            for f in fn:
                result.append(os.path.join(dp, f)[len(root) + 1:])
        return result

    def path_name(self, key):
        key = key.replace("/", "_")     # So naive yet...
        return os.path.abspath(os.path.join(self.root, key))

    def remove_empty_parents(self, path):
        parents = os.path.relpath(path, os.path.abspath(self.root))
        while len(parents) > 0:
            absparent = os.path.join(self.root, parents)
            if os.path.isdir(absparent):
                if len(os.listdir(absparent)) == 0:
                    os.rmdir(absparent)
                else:
                    break
            parents = os.path.dirname(parents)

    def open(self, key):
        try:
            return open(self.path_name(key), 'rb')
        except IOError as e:
            if 2 == e.errno:
                raise KeyError(key)
            else:
                raise

    def mkdir(self, path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError as e:
                if not os.path.isdir(path):
                    raise e

