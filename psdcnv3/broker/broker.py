# The entry point of PSDCNv3 broker

from ndn.app import NDNApp
from ndn.encoding import Name
from ndn.encoding.ndn_format_0_3 import parse_data
from ndn.types import InterestNack, InterestTimeout
import asyncio, aiofiles, base64, random, redis, datetime
import os, sys, pickle, json

from psdcnv3.psk import *
from psdcnv3.utils import *
from psdcnv3.broker.psodb import Pso
from psdcnv3.broker.logger import init_logger
# Must import all the possible choices for Names and Storage providers
from psdcnv3.names import TrieNames, ProcNames, RegexpNames
from psdcnv3.store import Store, TableStorage, RedisStorage, FileStorage, CacheWrapper
import psdcnv3.broker.handler

# For HTTP-based status report
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from threading import Thread
import platform, psutil

# Utilities
scoped_commands = {
    PSKCmd.commands["CMD_PA"]: "pubadvinfo",
    PSKCmd.commands["CMD_PU"]: "pubadvinfo",
    PSKCmd.commands["CMD_ST"]: "subinfo",
}
def scoped_command_info(command):
    return scoped_commands[command] if command in scoped_commands else None

def unparse_command(target, proto, dataname, seq=None):
    cmd_str = target + "/" + proto + dataname
    if seq:
        cmd_str += "/" + seq
    return cmd_str

def uptime(start):
    format = '%Y-%m-%d %H:%M:%S.%f'
    diff = datetime.datetime.strptime(str(datetime.datetime.now()), format) - \
       datetime.datetime.strptime(str(start), format)
    epapsed = ""
    days = diff.days; seconds = diff.seconds
    if days > 0: epapsed += str(days) + "D"
    hours = seconds // 3600 - diff.days * 24
    if hours > 0: epapsed += str(hours) + "h"
    minutes = seconds // 60 - hours * 60
    if minutes > 0: epapsed += str(minutes) + "m"
    epapsed += str(seconds % 60) + "s"
    return epapsed

class Broker(object):
    """
    PSDCNv3 broker running on NDN.

    Runs on a rendezvous node (RN) listening to PSDCNv3 Topic and Data requests,
    forwards them to appropriate RN if they are for other RNs,
    dispatches them to the appropriate handlers, and handles them in the PubSub spirit.

    :ivar id: unique identifier.
    :ivar app: an ndn.app.NDNApp instance.
    :ivar names: a names repository of datanames managed by this RN.
    :ivar store: a data repository managed by this RN.
    :ivar network: a list of RN names on which a broker instance will be running.
    :ivar psodb: a snapshot of PubSub operations.
    """

    handlers = dict()

    def __init__(self, id, app, names, store, psodb):
        self.id, self.app, self.names, self.store, self.psodb = id, app, names, store, psodb
        self.keeper = PSKCmd(app, node_name=id)
        self.pending_interests = {}
        self._start = datetime.datetime.now()        # For checking uptime
        # asyncio.get_event_loop().create_task(self.save_world())
        # asyncio.get_event_loop().create_task(self.delete_expired_interests())

    def start(self):
        """
        Connects to NFD and starts PSDCNv3 listeners by calling (awaiting) `self.listen`,
        and enters the main loop.
        """
        try:
            self.app.run_forever(after_start=self.launch())
        except KeyboardInterrupt:
            # loop = asyncio.get_event_loop()
            # loop.run_until_complete(self.save_world(periodic=False))
            # loop.run_until_complete(self.store.flush(periodic=False))
            pass

    def lookup_handler(command):
        command = 'psdcnv3.broker.handler.handle_' + command    # Regularise command name
        if command in Broker.handlers:
            handler = Broker.handlers[command]
        else:
            handler = eval(command)
            Broker.handlers[command] = handler
        return handler

    def on_pubsub_request(self, int_name, int_param, app_param, raw_packet):
        """
        Callback function awakened by any incoming packet for PubSub operation commands.
        """
        psk_parse = self.keeper.parse_command(int_name)
        prefix = psk_parse['prefix']
        command = psk_parse['command']
        # self.logger.debug(f"Inside Pubsub handler of {self.id} for {command}")
        asyncio.get_event_loop().create_task(self.dispatch(
            int_name, int_param, app_param, raw_packet, psk_parse))

    def on_admin_request(self, int_name, int_param, app_param):
        """
        Callback function awakened by any incoming packet for administrative commands.
        """
        psk_parse = self.keeper.parse_command(int_name)
        command = psk_parse['command']
        if command not in PSKCmd.commands.values():
            return
        prefix = psk_parse['prefix']
        # self.logger.debug(f"Inside Admin handler of {prefix} for {command}")
        asyncio.get_event_loop().create_task(Broker.lookup_handler(psk_parse['command'])(
            self, int_name, int_param, app_param, psk_parse))

    def on_data_request(self, int_name, int_param, app_param):
        """
        Callback function awakened by data requests whose route was registered previously.
        """
        freshness_period = 10000
        parsed_name = Name.to_str(int_name).split("/params-sha256")[0].split("/")[1:]
        built_name = "/" + "/".join(parsed_name)
        dataname = "/" + "/".join(parsed_name[:-1])
        suffix = parsed_name[-1]
        try:
            seq = int(suffix)
        except:
            seq = 0
        if seq <= 0:
            self.app.put_data(int_name, None, freshness_period=freshness_period)
            self.logger.debug(f"SD {built_name} discarded at {self.id}")
            return
        # self.logger.debug(f"Inside Data handler for {built_name}")
        packet = self.store.get(dataname, seq)
        if packet:
            self.logger.debug(f"SD {built_name} processed at {self.id}")
            # name, meta, _, _ = parse_data(packet)
            # assert Name.to_str(name) == built_name
            self.app.put_raw_packet(packet)
        elif int(seq) > 0:
            # Add to pending interest table with timestamp
            lifetime = int(int_param.lifetime) if int_param.lifetime else 4000
            timestamp = datetime.datetime.now()
            utc_time = timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            duration = lifetime / 1000
            expires = utc_time + duration
            # Check if any previous pending interest for the same data will live longer
            # than the new interest
            if (dataname, seq) in self.pending_interests:
                previous = self.pending_interests[(dataname, seq)]
                if previous - utc_time > duration:
                    # Merge by subsuming shorter expiry interest
                    self.logger.debug(
                        f"PI {built_name} is subsumed by an old one")
                    return
            self.pending_interests[(dataname, seq)] = expires
            # self.app.put_data(int_name, None, freshness_period=freshness_period)
            self.logger.debug(
                f'PI {built_name} expires in {int(duration)}"')
        else:
            # All other erroneous cases
            self.app.put_data(int_name, None, freshness_period=freshness_period)
            self.logger.debug(f"{built_name} not found at {self.id}")

    async def listen(self):
        """
        Coroutine function for listeners.

        Connects to NFD if `self.app` is still not connected to it,
        restores routes for data names if they are found in a broker backup, and
        registers listeners for the PubSub commands and administrative commands respectively.
        """
        # Restore routes if there are any of 'em
        await self.restore_routes(self.store.names())
        await self.restore_routes(self.local.names())
        # For pubsub commands
        await self.app.register(self.keeper.svc_name, self.on_pubsub_request, need_raw_packet=True)
        # For admin commands
        await self.app.register(self.id, self.on_admin_request)
        self.logger.info(f'Started listeners on {self.id}')

    async def launch(self):
        # Run services concurrently
        tasks = asyncio.gather(
            self.listen(),
            self.delete_expired_interests(),
            self.save_world(),
            self.store.flush(),
        )
        try:
            await tasks
        except asyncio.CancelledError:
            pass

    async def dispatch(self, int_name, int_param, app_param, raw_packet, psk_parse):
        """
        Examines a PubSub command, and perform necessary operations
        1) It was forwarded to me from another RN: do some administrative tasks and
           invokes an appropriate handler.
        2) This is the 1st-hop broker and the command demands immediate care in some way:
           do the necessary tasks (e.g. update psodb, register/unregister routes for data names,
           etc.), and
           - If the command needs to be handled directly by me (target broker is me,
             or the command is PD/SM/SL, or topicscope is LOCAL), calls an appropriate handler.
           - Otherwise, forward the command to the appropriate broker in the broker loop.
        """
        # Parse command using the PSK parser
        command = psk_parse['command']
        dataname = psk_parse['dataname']
        app_param = json.loads(bytes(app_param).decode() if app_param else "{}")

        first_hop = 'fwded_from' not in app_param
        app_param['fwded_from'] = self.id
        if 'rninfo' not in app_param or not app_param['rninfo']:
            app_param['rninfo'] = RNInfo(brokername=self.id)
        try:
            # Reflect PA and PU command to psodb
            if command == PSKCmd.commands["CMD_PA"] and first_hop:
                fresh = dataname not in self.psodb
                pubadvinfo = app_param['pubadvinfo']
                pubadvinfo['dataname'] = dataname
                # Check if the receiver is the first-hop broker
                if fresh:
                    await self.app.register(dataname, self.on_data_request)
                    self.logger.debug(f"PA registered route {dataname} at {self.id}")
                # Check if client wanted private storage rather than the broker storage
                where = pubadvinfo['storagetype'] \
                    if pubadvinfo['storagetype'] else StorageType.BROKER
                # if where == StorageType.BROKER:
                #     self.logger.debug(f"Broker {self.id} manages {dataname}")
                if where == StorageType.PUBLISHER or where == StorageType.DIFS:
                    storageprefix = param_value(app_param, "pubadvinfo", "storageprefix")
                    pubadvinfo['storageprefix'] = storageprefix
                    app_param['pubadvinfo'] = pubadvinfo
                    manager = "Publisher" if where == StorageType.PUBLISHER else "DIFS"
                    self.logger.debug(f"{manager} {storageprefix} manages {dataname}")
                # Add advertisement info to pubsub operations database 
                self.psodb.pubadv(dataname, pubadvinfo)
            elif command == PSKCmd.commands["CMD_PU"] and first_hop:
                if dataname in self.psodb:
                    await self.app.unregister(dataname)
                    self.logger.debug(f"PU unregistered route {dataname}")
                    self.psodb.pubunadv(dataname)
                else:
                    # Open Problem:
                    # Can it unregister route which is not one for the current broker?
                    self.logger.debug(f"PU {dataname} not found in psodb")
                self.store.delete(dataname)     # !!!
                # self.logger.debug(f"{self.id} won't manage {dataname} any more")
    
            # Check topicscope of operation for commands PA, PU, and ST
            topicscope = TopicScope.GLOBAL
            command_info = scoped_command_info(command)
            if command_info is not None:
                user_scope = param_value(app_param, scoped_commands[command], 'topicscope')
                if user_scope:
                    topicscope = int(user_scope)
    
            # Encode app_param
            enc_param = json.dumps(app_param).encode()

            # Check if the request can be processed immediately
            forward = int_param.forwarding_hint
            target = Name.to_str(forward[0][1]) if forward else arbit(dataname, self.network)
            def is_direct_command(command):
                return command in [
                    PSKCmd.commands["CMD_PD"],
                    PSKCmd.commands["CMD_SM"],
                    PSKCmd.commands["CMD_SL"],
                ]
            if target == self.id or is_direct_command(command) or topicscope == TopicScope.LOCAL:
                # Process the command immediately
                if topicscope == TopicScope.LOCAL:
                    target = self.id
                    self.logger.debug(f"{command} {dataname} processed by Data-RN {self.id}")
                await Broker.lookup_handler(command)(
                    self, int_name, int_param, enc_param, psk_parse)
            else:
                # Or else forward the request to target RN
                self.logger.debug(f"{command} {dataname} {self.id} => {target}")
                cmd_str = unparse_command(self.keeper.svc_name, command, dataname, psk_parse['seq'])
                int_param.forwarding_hint = [(1, target)]   # Adds FH to int_param
                int_param.lifetime = INT_LT_10
                _, _, content = await self.app.express_interest(
                    Name.from_str(cmd_str), interest_param=int_param, app_param=enc_param)
                self.app.put_data(int_name, content=content, freshness_period=1)
            if first_hop:
                if command == PSKCmd.commands["CMD_PA"]:
                    # Look for errors...
                    await self.ir_register(dataname, pubadvinfo, target, raw_packet)
                elif command == PSKCmd.commands["CMD_PU"]:
                    await self.ir_unregister(dataname, raw_packet)
            return
        except InterestTimeout as e:
            reason = f"InterestTimeout for {command} {dataname}"
        except InterestNack as e:
            reason = f"InterestNack {e.reason} for {command} {dataname}"
        except Exception as e:
            reason = f"{type(e).__name__} {str(e)}"
            # reason = f"Command dispatch error"
        response = {'status': 'ERR', 'reason': reason}
        self.app.put_data(int_name, content=json.dumps(response).encode(), freshness_period=1)
        self.logger.error(reason)

    async def delete_expired_interests(self):
        await asyncio.sleep(30.0)           # Should it be configurable?
        timestamp = datetime.datetime.now()
        utc_time = timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
        for pending in list(self.pending_interests):
            dataname, seq = pending
            if utc_time > self.pending_interests[pending]:
                del self.pending_interests[pending]
                self.logger.debug(f'PI {dataname}/{seq} expired')
        asyncio.get_event_loop().create_task(self.delete_expired_interests())

    async def save_world(self, periodic=True):
        if periodic:
            await asyncio.sleep(60.0)       # Should it be configurable?
        path = world_name(self.id)
        # if os.path.isfile(path): os.rename(path, path + ".0")
        world = {
            'names': self.names.pickle(),   # Global topic tree
            'local': self.local.pickle(),   # Local topic tree
            'store': self.store.pickle(),   # Last written data indices information
            'psodb': self.psodb.pickle(),   # Advertised names for which data are kept here
        }
        async with aiofiles.open(path, "wb") as f:
            await f.write(pickle.dumps(world))
            await f.flush()
        if periodic:
            asyncio.get_event_loop().create_task(self.save_world(periodic=True))

    async def restore_routes(self, datanames):
        for dataname in datanames:
            try:
                await self.app.register(dataname, self.on_data_request)
                self.logger.debug(f"Restored route {dataname} at {self.id}")
            except:
                pass

    def restore_world(self):
        path = world_name(self.id)
        if not os.path.isfile(path):
            return
        with open(path, "rb") as f:
            world = pickle.loads(f.read())
            self.names.restore(world['names'])
            self.local.restore(world['local'])
            self.store.restore(world['store'])
            self.psodb.restore(world['psodb'])
        self.logger.info(f"Restored broker {self.id}'s world")
        names_count = self.names.count() + self.local.count()
        self.logger.debug(
            f"{self.id} has {names_count} data names and {self.store.count()} store items")

    async def ir_register(self, dataname, pubadvinfo, target, raw_packet):
        ir_cmd, int_param, _ = self.keeper.make_irreg_cmd(self.ir_prefix, dataname)
        ir_app = {}
        ir_app['advinfo'] = pubadvinfo
        ir_app['topic_rn'] = target
        ir_app['data_rn'] = self.id
        ir_app['packet_'] = base64.b64encode(raw_packet).decode("cp949")
        ir_app = json.dumps(ir_app).encode()
        try:
            await self.app.express_interest(Name.from_str(ir_cmd), interest_param = int_param,
                app_param=ir_app)
        except Exception as e:
            # self.logger.error(f"PA couldn't register {dataname} to IR")
            pass

    async def ir_unregister(self, dataname, raw_packet):
        ir_cmd, int_param, _ = self.keeper.make_irdel_cmd(self.ir_prefix, dataname)
        try:
            await self.app.express_interest(Name.from_str(ir_cmd), interest_param=int_param)
            # self.logger.debug(f"IR unregistered {dataname}")
        except Exception as e:
            # self.logger.debug(f"PU couldn't unregister {dataname} from IR")
            pass

    def report(self, window=0):
        date_format_str = "%Y/%m/%d %H:%M:%S"
        # Broker information
        configs = {}
        configs['broker_id'] = self.id
        configs['description'] = f'PubSub broker running on {platform.node()}'
        configs['version'] = 'PSDCNv3 (asyncio) Release D+'
        managers = {}
        managers['name_manager'] = type(self.names).__name__
        managers['storage_manager'] = self.storage_manager
        configs['managers'] = managers
        hardware = {}
        hardware['cpu'] = {
            "model_name": f"[{platform.machine()}] {platform.processor()}",
            "cpu_cores": psutil.cpu_count()
        }
        mem_info = psutil.virtual_memory()
        hardware['memory'] = {
            'total': mem_info.total,
            'available': mem_info.available
        }
        configs['hardware'] = hardware
        configs['os_platform'] = platform.platform()
        # Broker status
        status = {}
        status['time'] = {
            'start': self._start.strftime(date_format_str),
            'current': datetime.datetime.now().strftime(date_format_str),
            'uptime': uptime(self._start)
        }
        advertised = {}
        globals_ = list(self.names.names())
        locals_ = list(self.local.names())
        names_count = len(globals_) + len(locals_)
        window_size = names_count if not window else int(window)
        window_size = min(names_count, config_default('status_report_window_size', window_size))
        advertised['total'] = len(globals_) + len(locals_)
        advertised['window_size'] = window_size
        advertised['names'] = globals_[-window_size:]
        advertised['local_names'] = locals_[-window_size:]
        status['advertised'] = advertised
        published = {}
        pubs = list(self.store.names())
        pubs_len = len(pubs)
        pubs_win = pubs_len if not window else int(window)
        pubs_win = min(pubs_len, pubs_win, config_default('status_report_window_size', pubs_len))
        published['total'] = pubs_len
        published['window_size'] = pubs_win
        manifests = []
        for dataname in list(self.store.names())[-pubs_win:]:
            md = self.store.metadata[dataname]
            mi = {'name': dataname, 'fst': md.fst, 'lst': md.lst}
            manifests.append(mi)
        published['manifest'] = manifests
        status['published'] = published
        # Report made
        return {'config': configs, 'status': status}

def world_name(name):
    return "node" + build_path(name) + '.world'

def check_id(argv):
    return argv[1] if len(argv) > 1 else config_default("broker_prefix", "/rn-1")

### An HTTP-based Status Monitor
class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=cp949") # utf-8
        self.end_headers()
        self.wfile.write(bytes(json.dumps(broker.report(), indent=2), "cp949"))   # utf-8

    def log_message(self, *rest):
        pass

class StatusMonitor(Thread):
    def __init__(self, broker, hostname, port):
        super().__init__()
        self.broker = broker
        self.hostname = hostname
        self.port = port
        self.daemon = True

    def run(self):
        server = HTTPServer((self.hostname, self.port), StatusHandler)
        # broker.logger.debug(f"Status Server started at http://{self.hostname}:{self.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        server.server_close()
        broker.logger.info(f"Status server stopped")

# The GRAND Main
def main():
    """
    Entry point of the broker.

    Loads confiuration parameters,
    Initializes broker contexts such as Names(GLOBAL and LOCAL), Store and Storage,
    Initializes logger using the confurations data,
    Wraps a cache arount the storage if needed,
    Restore previous world if one exists.
        A world consists of Names, Store, and Psodb.
    Clear store if requested in order to clean up data populated during previous sessions.
    Loads `network` of RNs information for DHT arbitration.
    Starts related listeners by calling `self.start`.
    """
    global broker

    broker = Broker(check_id(sys.argv), NDNApp(),
        eval(config_default("names_provider", "TrieNames()")),
        Store(eval(config_default("storage_provider", "TableStorage()"))),
        Pso()
    )
    broker.local = eval(config_default("names_provider", "TrieNames()"))
    # Initialize psdcnv3 logger
    broker.logger = init_logger()
    # Add cache to storage if cache_size was specified
    cache_size = config_default("cache_size", 0)
    if cache_size > 0:
        storage_manager = f"{broker.store.media()} with a cache of {cache_size} cells"
        broker.store.set_storage(CacheWrapper(broker.store.get_storage(), cache_size))
    else:
        storage_manager = f"{broker.store.media()}"
    broker.storage_manager = storage_manager
    broker.logger.debug(f"{storage_manager}")
    # Add broker context info to submodules
    broker.names.set_context(broker)
    broker.store.set_context(broker)
    # In case of warm restart
    broker.restore_world()
    if config_default("clear_store", False):
        broker.store.clear()
    # Here we go!
    broker.network = config_default("network", ['/rn-1'])
    broker.validate = config_default("service_token_validation", False)
    broker.ir_prefix = config_default("IR_prefix", "/marketplace")
    # Add status monitor endpoint
    status_endpoint = config_default("status_monitor", None)
    broker.status = None
    broker.status_chunk_size = int(config_default("status_chunk_size", "8192"))
    if status_endpoint is not None:
        status_endpoint = urlparse(status_endpoint)
        status_monitor = StatusMonitor(broker, status_endpoint.hostname, status_endpoint.port)
        status_monitor.start()
    # Start the main event loop
    broker.start()

if __name__ == '__main__':
    main()

