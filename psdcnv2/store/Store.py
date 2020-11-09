import asyncio, pickle, logging
import math

class Store(object):
    """
    Data store abstraction for PSDCNv2.

    A store wraps a full-fledged storage which actually maintaines published data
        where the storage is an instance of `Storage` provider.
    Write is done in an indexed manner. Write to a name increases the size of the cell
        related to the name, and write the data to the last index position.
    Read is also done in an indexed manner.
        It can read from a specific index position of the cell for the given name.
        If not given an index, the last position is read.
    For read/write operations, the index of a cell starts at 0(zero).
    Store periodically flushes(drains) memory resident data to the actual storage.

    :ivar storage: storage provider instance
    :ivar metadata: table for data name to data value metadata information
    """

    def __init__(self, storage):
        """
        :param storage: storage provider instance which actually maintained data.
        """
        self.storage = storage
        self.metadata = {}
        asyncio.get_event_loop().create_task(self.flush(periodic=True))

    def __str__(self):
        return f"{self.storage} with metadata {self.metadata}"

    def __contains__(self, name):
        """
        Checks if the given `name` has a valid storage cell.

        :param name: name of the cell to which data will be published.
        :return: True of the `name` has a valid storage cell.
        """
        return name in self.metadata

    def end(self, name):
        """
        Retrieves the last position of the cell for the given `name`.

        :param name: name of the cell to which published data will be stored.
        """
        return self.metadata[name].lst if name in self.metadata else 0

    def get_storage(self):
        return self.storage

    def set_storage(self, storage):
        self.storage = storage

    def media(self):
        return self.storage.media()

    def set_context(self, context):
        self.logger = context.logger
        self.storage.set_context(context)

    def get(self, name, seq=0):
        """
        Retrives data stored at index `seq` of the cell for the given name `name`.
        If `seq` (which defaults to 0) is not positive, data is retrived from the last
            index position of the cell. If it is 0, it means last position,
            and -1, the value before the last position, etc.

        :param name: name of the cell to which data will be fetched.
        :param seq: position of the cell for the the given `name`.
        :return: fetched value of the given position `name`#`seq`
        """
        end = self.end(name)
        if end == 0:
            return None
        idx = seq = int(seq)
        if idx > end:
            return None
        elif idx <= 0:
            idx += end          # 0 points to last, -1 points to 1 before last, ...
        md = self.metadata[name]
        if md.fst <= idx:
            value = self.storage.get(storage_name(name, idx))
            return value.decode() if value else None
        _sseq = str(seq)
        if seq != idx:
            _sseq += "("+ str(idx) + ")"
        if md.bun is not None:
            bundlesize = md.bun.size
            b_idx = int(math.ceil(idx / bundlesize))
            b_pos = (idx - 1) % bundlesize
            bundle = self.get_bundle(name, b_idx)
            if bundle is None:
                self.logger.warning(f"Bundle {b_idx} for {name}[{_sseq}] not found")
                return None
            self.logger.debug(f"{name}[{_sseq}] found in bundle {b_idx}[{b_pos+1}]")
            return bundle[b_pos].decode()
        else:
            self.logger.warning(f"Seq# {_sseq} doet't make sense for {name}")
            return None

    def get_bundle(self, name, idx):
        bundle = self.storage.get(bundle_name(name, idx))
        return pickle.loads(bundle) if bundle is not None else None

    def set(self, name, value, seq=0, pso=None):
        """
        Writes `value` to the given `seq` position of the cell for the given `name`,
            and increases the size of the cell accordingly.
            If it is the first written `value` for `name`, the position is set to 0.

        :param name: name of the cell to which published data (`value`) will be stored.
        :param value: data value to be stored.
        :param seq: position number of the cell to which `value` will be stored.
        :return: index of the position where the data value is stored.
        """
        end = self.end(name)
        seq = int(seq)
        idx = seq if seq > 0 else end + seq + 1
        # Newly seen name
        if name not in self.metadata:
            b_size = 0
            if pso is not None:
                if 'bundlesize' in pso:
                    b_size = int(pso['bundlesize'])
                    self.logger.debug(f"{name}'s bundlesize is {b_size}")
            self.metadata[name] = Metadata(name, fst=1, lst=1, bundlesize=b_size)
        md = self.metadata[name]
        if idx < md.fst:
            self.logger.warning(f"Can't write to {name}[{seq}] for bundled data")
            return idx
        bundle = md.bun is not None
        # Check if position to write is beyond a bundle size
        if bundle and idx >= md.fst + md.bun.size:
            try:
                self.metadata[name].bun.count += 1
                b_idx = self.metadata[name].bun.add_bundle(name, [
                    self.get(name, seq).encode() for seq in range(md.fst, md.lst + 1)], self)
                self.logger.debug(f"Moved {name}[{md.fst}-{md.lst}] to bundle {b_idx}")
                self.delete_range(name, md.fst, md.lst)
            except:
                self.logger.debug(f"Data for {name}[{md.fst}-{md.lst}] to bundle not found")
            self.metadata[name].fst = self.metadata[name].lst + 1
        self.metadata[name].lst = idx
        # Actually write the data to the storage
        self.storage.set(storage_name(name, idx), str(value).encode())
        return idx

    def delete(self, name):
        """
        Removes the cell for `name` and invalidates all further read/write requests to it.

        :param name: name of the cell to which published data will be stored.
        """
        if name in self.metadata:
            end = self.metadata[name].lst
            for idx in range(end + 1):
                self.storage.delete(storage_name(name, idx))
            del self.metadata[name]

    def delete_range(self, name, fst, lst):
        if name in self.metadata:
            for idx in range(fst, lst + 1):
                self.storage.delete(storage_name(name, idx))
            self.logger.debug(f"Deleted {name}'s orphaned data range {fst}-{lst}")

    def names(self):
        """
        Returns list of data cell names maintained in the store.
        """
        return self.metadata.keys()

    def count(self):
        """
        Returns number of cells maintained in the store.
        """
        return len(self.names())

    def clear(self):
        """
        Removes all the cells and the cell names from the store.
        """
        self.storage.clear()
        self.metadata.clear()

    def pickle(self):
        """
        Saves cells and indices information of the store to a byte array.
        """
        return pickle.dumps(self.metadata)

    def restore(self, pickled):
        """
        Reinitializes the store with the cells and indices information saved
            at `pickled`. Related data values will be restored from
            permanent storage as needed.
        """
        self.metadata = pickle.loads(pickled)
        self.storage.restore()

    async def flush(self, periodic=True):
        if periodic:
            await asyncio.sleep(3600)       # 1 hour
        try:
            self.storage.flush()
        except:
            pass
        if periodic:
            asyncio.get_event_loop().create_task(self.flush(periodic=True))
# Store

PSDCNv2Store = Store                    # Alias

class Metadata(object):
    def __init__(self, name, fst=0, lst=0, bundlesize=0):
        # Initialize name(dataname), fst and lst, and bundle
        self.name = name
        self.fst = fst
        self.lst = lst
        self.bun = Bundle(size=bundlesize) if bundlesize > 0 else None
        pass

    def __str__(self):
        return f"{self.name}: range={self.fst}-{self.lst}, bundles={str(self.bun)}"
    

class Bundle(object):
    def __init__(self, size):
        self.size = size
        self.count = 0

    def __str__(self):
        return f"(size={self.size}, count={self.count})"

    def add_bundle(self, name, values, store):
        store.storage.set(bundle_name(name, self.count), pickle.dumps(values))
        return self.count

# Helpers
def storage_name(name, seq):
    return f'v{name}[{seq}]'

def bundle_name(name, seq):
    return f'b{name}[{seq}]'
