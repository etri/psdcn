from ndn.app import NDNApp
from ndn.encoding import Name
from ndn.types import InterestNack
import psdcnv2.broker.handler
import asyncio, aiofiles, random, redis, datetime
import os, sys, re, pickle, json

from psdcnv2.psk import PSKCmd
from psdcnv2.broker.psodb import PSO
from psdcnv2.names import TrieNames, ProcNames, RegexpNames
from psdcnv2.store import Store, TableStorage, RedisStorage, FileStorage, CacheWrapper
from psdcnv2.utils import config_value, init_logger, build_path

class Broker(object):
    """
    PSDCNv2 broker running on NDN.

    Runs on a rendezvous node (RN) listening to PSDCNv2 Topic and Data requests,
    dispatches them to the appropriate handlers, and handles them in the PubSub manner.

    :ivar id: unique identifier for the RN.
    :ivar app: an ndn.app.NDNApp instance.
    :ivar names: a names repository of datanames managed by this RN.
    :ivar store: a data repository managed by this RN.
    :ivar network: a list of RN names on which a broker instance will be running.
    """

    def __init__(self, id, app, names, store, psodb):
        self.id, self.app, self.names, self.store, self.psodb = id, app, names, store, psodb
        self.keeper = PSKCmd(app, bro_name=id)
        self.pending_interests = []
        self.epoch = datetime.datetime.now()        # For checking time alive
        asyncio.get_event_loop().create_task(self.save_world())
        asyncio.get_event_loop().create_task(self.delete_expired_interests())

    def start(self):
        """
        Connects to NFD and starts PSDCNv2 listeners by calling (awaiting) `self.listen`,
        and enters the main loop.
        """
        try:
            self.app.run_forever(after_start=self.listen())
        finally:
            # Main-loop finished.
            # Save names and store to permanent storage for future restoration.
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.save_world(periodic=False))
            loop.run_until_complete(self.store.flush(periodic=False))

    def on_data_rn_interest(self, int_name, int_param, app_param, raw_packet=None):
        """
        Callback function awakened by any incoming packet to the Data RN.
        """
        psk_parse = self.keeper.parse_command(int_name)
        asyncio.get_event_loop().create_task(
            psdcnv2.broker.handler.dispatch(self,
                int_name, int_param, app_param, raw_packet, psk_parse))

    def on_topic_rn_interest(self, int_name, int_param, app_param, raw_packet=None):
        """
        Callback function awakened by any incoming packet to the Topic RN.
        """
        psk_parse = self.keeper.parse_command(int_name)
        asyncio.get_event_loop().create_task(
            eval('psdcnv2.broker.handler.handle_' + psk_parse['command'])(
                self, int_name, int_param, app_param, raw_packet, psk_parse))

    async def listen(self):
        """
        Coroutine function for startning listeners.

        Connects to NFD if `self.app` still not connected to it, and registers
        callbacks for Data RN and Topic RN accordingly.
        """
        await self.app.register(self.keeper.net_name, self.on_data_rn_interest,
            need_raw_packet=True)
        await self.app.register(self.id, self.on_topic_rn_interest, need_raw_packet=True)
        self.logger.info(f'Started listeners on {self.id}')

    async def delete_expired_interests(self):
        await asyncio.sleep(30.0)           # Should it be configurable?
        timestamp = datetime.datetime.now()
        utc_time = timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
        for pending in self.pending_interests[:]:
            dataname, seq, _, expires = pending
            if utc_time > expires:
                self.pending_interests.remove(pending)
                self.logger.debug(f'Interest {dataname}[{seq}] expired at {int(expires)}')
        asyncio.get_event_loop().create_task(self.delete_expired_interests())

    async def save_world(self, periodic=True):
        if periodic:
            await asyncio.sleep(60.0)       # Should it be configurable?
        path = world_name(self.id)
        # if os.path.isfile(path):
        #     os.rename(path, path + ".0")
        world = {
            'names': self.names.pickle(),   # Published names
            'store': self.store.pickle(),   # Last written data indices and bundles information
            'psodb': self.psodb.pickle(),   # Advertised names for which data are kept here
        }
        async with aiofiles.open(path, "wb") as f:
            await f.write(pickle.dumps(world))
            await f.flush()
        # with open(path, "wb") as f:
        #     f.write(pickle.dumps(world))
        #     f.flush()
        # self.logger.info(f"Broker {self.id}'s names saved on {path}")
        if periodic:
            asyncio.get_event_loop().create_task(self.save_world(periodic=True))

    def restore_world(self):
        path = world_name(self.id)
        if not os.path.isfile(path):
            return
        with open(path, "rb") as f:
            world = pickle.loads(f.read())
            self.names.restore(world['names'])
            self.store.restore(world['store'])
            self.psodb.restore(world['psodb'])
        self.logger.info(f"Restored broker {self.id}'s world")
        self.logger.debug(
            f"{self.id} has {self.names.count()} data names and {self.store.count()} store items")

def world_name(name):
    return "node" + build_path(name) + '.world'

def config(name, default):
    value = config_value(name)
    return value if value else default

def check_id(argv):
    return argv[1] if len(argv) > 1 else config("broker_prefix", "/rn-1")

def main():
    """
    Entry point of the broker.

    Loads confiuration parameters,
    Initializes logger using the confurations data,
    Makes a `Broker` instance with an NDNApp instance, appropriate id, names, store, pso
        initialized and configured as specified in the configuration file.
    Restore previous world if one exists.
        A world consists of advertised data names and published data names with indices.
    Clear store if requested (to clean up data populated at other sessions).
    Loads `network` of RNs information for DHT arbitration.
    Starts related listeners by calling `self.start`.
    """
    broker = Broker(check_id(sys.argv), NDNApp(),
        eval(config("names_provider", "TrieNames()")),
        Store(eval(config("storage_provider", "TableStorage()"))),
        PSO()
    )
    # Initialize psdcnv2 logger
    broker.logger = init_logger()
    # Add cache to storage if cache_size was specified
    cache_size = config("cache_size", 0)
    if cache_size > 0:
        broker.logger.debug(f"{broker.store.media()} with cache of size {cache_size}")
        broker.store.set_storage(CacheWrapper(broker.store.get_storage(), cache_size))
    else:
        broker.logger.debug(f"Storage is {broker.store.media()}")
    # Add context info to submodules
    broker.names.set_context(broker)
    broker.store.set_context(broker)
    # In case of warm restart
    broker.restore_world()
    if config("clear_store", False):
        broker.store.clear()
    # Here we go!
    broker.network = config("network", ['/rn-1'])
    broker.validate = config("service_token_validation", False)
    broker.ir_prefix = config("IR_prefix", "/marketplace")
    broker.start()

if __name__ == '__main__':
    main()
