from ndn.encoding import Name
from ndn.encoding.ndn_format_0_3 import parse_data
from ndn.utils import gen_nonce
from ratelimit import limits
import asyncio, pickle, base64, random, logging, json, math
import sys

from psdcnv3.psk import *
from psdcnv3.utils import *
from psdcnv3.store.Store import Metadata

### UTILITIES ###
def check_rate(def_rate):
    """
    Look up rate limit value from configuration value "service_rate".
        If the limit value is not defined, use `def_rate` instead.
    """
    rate = config_value("service_rate")
    return int(rate) if rate is not None else def_rate

def validate(broker, dataname, servicetoken):
    """
    Simple stub for service token validation.
    Works only for dataname /test/validation and service token "hasta la vista"
    """
    if not broker.validate:
        return True
    if dataname == "/test/validation":
        return servicetoken == "hasta la vista"
    return True

def answer(broker, int_name, status='OK', value=None, reason=None):
    response = {}
    response['status'] = status
    if value is not None:
        response['value'] = value
    if reason is not None:
        response['reason'] = reason
    broker.app.put_data(int_name,
        content=json.dumps(response).encode(), freshness_period=1)


### PUB/SUB HANDLERS ###

### PUBADV (PA) Handler ###
async def handle_PA(broker, int_name, int_param, app_param, psk_parse):
    app_param = json.loads(bytes(app_param).decode())
    pubadvinfo = app_param['pubadvinfo']
    topicscope = int(pubadvinfo['topicscope'])
    rn_name = param_value(app_param, 'rninfo', 'brokername')
    dataname = psk_parse['dataname']
    pubadvinfo['dataname'] = dataname
    response = {'new_rn': rn_name}

    # Chek if dataname was already advertised before
    def redefine_or_decline(condition, names, rn_name, dataname, extra_flag, response):
        if condition:
            names.advertise(rn_name, dataname, extra_flag)
            response['status'] = "OK"
            action = "redefined"
        else:
            response['status'] = "ERR"
            response['reason'] = "Redefine"
            action = "declined"
        return action

    redefine = param_value(app_param, 'pubadvinfo', 'redefine')
    if dataname in broker.names:
        response['old_rn'] = broker.names[dataname].rn_names[-1]
        pub_moved = param_value(app_param, 'pubadvinfo', 'pub_moved')
        action = redefine_or_decline(bool(redefine) or pub_moved,
            broker.names, rn_name, dataname, pub_moved, response)
    elif dataname in broker.local:
        action = redefine_or_decline(bool(redefine),
            broker.local, rn_name, dataname, False, response)
    else:
        # Really advertise dataname
        action = "advertised"
        if topicscope == TopicScope.GLOBAL:
            broker.names.advertise(rn_name, dataname)
        else:
            broker.local.advertise(broker.id, dataname)
            action += " locally"
        response['status'] = "OK"

    # Check if client wanted self storage rather than the broker storage
    if 'storageprefix' in pubadvinfo:
        storageprefix = pubadvinfo['storageprefix']
        if storageprefix:
            broker.names[dataname].storageprefix = storageprefix
            response['storageprefix'] = storageprefix
            rn_name = storageprefix

    # All done
    broker.logger.info(f"PA {action} {dataname}@{rn_name}")
    response['broker'] = broker.id
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)
# End handle_PA

### PUBUNADV (PU) Handler ###
async def handle_PU(broker, int_name, int_param, app_param, psk_parse):
    app_param = json.loads(bytes(app_param).decode())
    pubadvinfo = app_param['pubadvinfo']
    topicscope = int(pubadvinfo['topicscope'])
    dataname = psk_parse['dataname']
    response = {}
    response['broker'] = broker.id

    names_tree = broker.names if topicscope == TopicScope.GLOBAL else broker.local
    if dataname not in names_tree:
        response['status'] = "ERR"
        response['reason'] = "Undefined"
        broker.logger.debug(f"PU {dataname} undefined")
    else:
        names_tree.unadvertise(dataname)
        broker.logger.info(f"PU {dataname} 2")
        response['status'] = "OK"

    # Return response
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)
# End handle_PU

### PUBDATA (PD) Handler ###
async def handle_PD(broker, int_name, int_param, app_param, psk_parse):
    dataname = psk_parse['dataname']
    seq1 = int(psk_parse['seq'])

    ### MOBILITY stuff
    if dataname not in broker.psodb:
        broker.logger.debug(f"PD {dataname} is new to me. Pub moved?")
        # Publisher moved to a new broker!
        # (Re)Advertise dataname to reflect the new Data-RN name
        topic_rn = arbit(dataname, broker.network)
        success = True
        pubadvinfo_m = PubAdvInfo(dataname)
        pubadvinfo_m['pub_moved'] = True
        if topic_rn != broker.id:
            # Advertise the name to Topic-RN
            command, int_param, apq_param = \
                broker.keeper.make_pubadv_cmd(topic_rn, dataname,
                    pubadvinfo=pubadvinfo_m, rninfo=RNInfo(brokername=broker.id))
            _, _, content = await broker.app.express_interest(
                Name.from_str(command), interest_param=int_param, app_param=apq_param)
            content = json.loads(bytes(content).decode())
            if 'old_rn' in content:
                old_rn = content['old_rn']
                new_rn = content['new_rn']
                # Fetch Pso and Storage metadata from the original Data-RN
                command, int_param, _ = \
                    broker.keeper.make_generic_cmd("Metadata", prefix=old_rn, dataname=dataname)
                _, _, content = \
                    await broker.app.express_interest(Name.from_str(command), 
                        interest_param=int_param, must_be_fresh=True)
                broker.logger.debug(f"PD copied metadata {dataname} from {old_rn}")
                content = json.loads(bytes(content).decode())
                store_md = pickle.loads(base64.b64decode(content['store_md'].encode()))
                if 'pso_info' in content:
                    pubadvinfo_m = content['pso_info']
                else:
                    pubadvinfo_m = PubAdvInfo(dataname=dataname)
                store_md.fst = store_md.lst + 1
                broker.store.metadata[dataname] = store_md
                broker.logger.debug(f"PD re-advertised {dataname} from {old_rn} to {new_rn}")
            else:
                broker.logger.debug(f"PD re-advertise failed. Old RN not found")
                success = False
        else:
            # Append current node to the list of rn_names
            broker.names.advertise(broker.id, dataname, pub_moved=True)
            broker.logger.debug(f"PD adversised {dataname}@{broker.id}")
        if success:
            broker.psodb.pubadv(dataname, pubadvinfo_m)
            await broker.app.register(dataname, broker.on_data_request)
            broker.logger.debug(f"PD registered route {dataname}@{broker.id}")
        else:
            reason = f"{dataname} not advertised yet."
            answer(broker, int_name, status='ERR', reason=reason)
            broker.logger.debug(f"PD failed. {reason}")
            return
    ### End MOBILITY

    ### Reject publication for non-broker managed store
    pubadvinfo = broker.psodb[dataname]
    if 'storageprefix' in pubadvinfo:
        storageprefix = pubadvinfo['storageprefix']
        if storageprefix and (storageprefix != broker.id):
            # Publisher or DIFS storage requested
            reason = f"Publish to {storageprefix} instead"
            broker.logger.debug(f"PD publication to {broker.id} failed. {reason}")
            answer(broker, int_name, status='storage type', reason=reason)
            return

    # Gather data items for publication using a fetcher
    app_param = json.loads(app_param.decode())
    prefix = param_value(app_param, 'pubdatainfo', 'data_prefix')
    seq2 = int(param_value(app_param, 'pubdatainfo', 'data_eseq'))
    pub_prefix = param_value(app_param, 'pubdatainfo', 'pub_prefix')
    seq_, plural = (f"-{seq2}", "s") if seq1 != seq2 else ("", "")
    forwarding_hint = [(0, pub_prefix)] if pub_prefix else []
    broker.logger.debug(f"PD {prefix}/{seq1}{seq_} pub_prefix={pub_prefix}")
    seqs = list(range(seq1, seq2+1))
    vals = []
    async for _, _, _, packet in \
            segment_fetcher(broker.app, prefix, seq1, seq2,
                forwarding_hint=forwarding_hint, lifetime=INT_LT_10):
        vals.append(packet)     # Collects only raw packets
    
    # Check if data all the data items were collected
    if len(seqs) != len(vals):
        lost = len(seqs) - len(vals)
        answer(broker, int_name, status="ERR", reason=f"PD lost {lost} item{plural}")
        return

    # All the expected data items ready. Put them in the Store.
    broker.logger.debug(f"PD {prefix}/{seq1}{seq_} ({len(vals)} item{plural})")
    actual = 0
    for seq, val in zip(seqs, vals):
        pos = broker.store.set(dataname, val, seq)
        loc = f"{dataname}/{pos}"
        if pos <= 0:
            broker.logger.error(f"PD ignoring invalid location {loc}")
            continue
        actual += 1
        broker.logger.info(f"PD published to {loc}")
        # See if there are pending interests and process them
        for data_name, seq_no in list(broker.pending_interests):
            if dataname == data_name and pos == seq_no:
                broker.app.put_raw_packet(val)  # val is a raw packet
                del broker.pending_interests[(data_name, seq_no)]
                broker.logger.debug(f"PI {loc} processed")

    # Report number of data items published
    answer(broker, int_name, value=actual)
# End handle_PD

### SUBTOPIC (ST) Handler ###
async def handle_STx(broker, app_param, topicname, external):
    """
    Shared by both handle_ST and handle_SL
    """
    names_tree = broker.names if external else broker.local
    matches = [(slot.dataname, slot.rn_names 
                 if not hasattr(slot, 'storageprefix') else [slot.storageprefix])
        for slot in names_tree.matches(topicname)]
    if not broker.validate:
        return matches
    # Validate matches against the service token
    app_param = json.loads(bytes(app_param).decode())
    servicetoken = param_value(app_param, 'subinfo', 'servicetoken')
    collect = []
    for match in matches:
        name, _ = match
        if validate(broker, name, servicetoken):
            collect.append(match)
        elif external:
            broker.logger.debug(f"ST {name} service token validation error")
    return collect

@limits(calls=int(check_rate(100)*100), period=100)
async def handle_ST(broker, int_name, int_param, app_param, psk_parse):
    topicname = psk_parse['dataname']
    response = await handle_STx(broker, app_param, topicname, external=True)
    broker.logger.info(f"ST {topicname} has {len(response)} matches at {broker.id}")
    answer(broker, int_name, value=response)
# End handle_ST

### SUBMANI (SM) Handler ###
async def handle_SMx(broker, dataname, external):
    """
    Shared by both handle_SM and handle_SL
    """
    response = {}
    if dataname in broker.store:
        md = broker.store.metadata[dataname]
        response['dataname'] = dataname
        response['rn_name'] = broker.id
        response['fst'] = md.fst
        response['lst'] = md.lst
        if external:
            response['status'] = "OK"
            broker.logger.info(f"SM {dataname} served at {broker.id}")
    elif external:
        response['status'] = "ERR"
        response['reason'] = f"{dataname} not found at {broker.id}"
        broker.logger.info(f"SM {dataname} not found at {broker.id}")
    return response

async def handle_SM(broker, int_name, int_param, app_param, psk_parse):
    response = await handle_SMx(broker, psk_parse['dataname'], external=True)
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)
# End handle_SM

### SUBLOCAL (SL) Handler ###
@limits(calls=int(check_rate(100)*100), period=100)
async def handle_SL(broker, int_name, int_param, app_param, psk_parse):
    topicname = psk_parse['dataname']
    matches = await handle_STx(broker, app_param, topicname, external=False)
    collect = []
    for dataname, _ in matches:
        manifest = await handle_SMx(broker, dataname, external=False)
        if manifest:
            collect.append((dataname, manifest['fst'], manifest['lst']))
    response = {
        'broker': broker.id,
        'manifests': collect
    }
    broker.logger.info(f"SL {topicname} has {len(collect)} matches at {broker.id}")
    answer(broker, int_name, value=response)
# End of handle_SL


### ADMIN COMMAND HANDLERS ###

### Status Handler ###
async def handle_Status(broker, int_name, int_param, app_param, psk_parse):
    c_size = broker.status_chunk_size
    seq = psk_parse['seq']
    seq = int(seq) if seq is not None else 1
    def make_chunk(n):
        return broker.status[(n-1)*c_size:n*c_size]
    if seq <= 1:
        app_param = json.loads(bytes(app_param).decode()) if app_param else {}
        window = app_param['window_size'] if 'window_size' in app_param else None
        window = int(window) if window is not None \
                             else config_default('status_report_window_size', 0)
        broker.status = json.dumps(broker.report(window))
        broker.status_chunks = math.ceil(len(broker.status) / c_size)
        response = json.dumps({'count': broker.status_chunks, 'chunk': make_chunk(1)}).encode()
        broker.app.put_data(int_name, content=response, freshness_period=1)
    else:
        broker.app.put_data(int_name, content=make_chunk(seq).encode(), freshness_period=1)
    if seq == broker.status_chunks:
        broker.status = None
        # broker.logger.debug(f"Status/report {broker.id} sent {broker.status_chunks} chunks")

### Network Handler ###
async def handle_Network(broker, int_name, int_param, app_param, psk_parse):
    action = psk_parse['dataname']
    if action == '/set':
        app_param = json.loads(bytes(app_param).decode())
        rn_names = list(param_value(app_param, 'rninfo', 'brokername'))
        broker.network = rn_names
        answer(broker, int_name)
        broker.logger.info(f"Network/set {broker.id}'s network")
    elif action == '/discover':
        response = {'brokers': broker.network}
        response = json.dumps(response).encode()
        broker.logger.info(f"Network/discover at {broker.id}")
        broker.app.put_data(int_name, content=response, freshness_period=1)
    else:
        reason = f"Unknown action {action} for command 'Network'"
        answer(broker, int_name, status='ERR', reason=reason)
        broker.logger.error(reason)

### Save Handler ###
async def safe_save(broker):
    await broker.save_world(periodic=False)
    await broker.store.flush(periodic=False)

async def handle_Save(broker, int_name, int_param, app_param, psk_parse):
    await safe_save(broker)
    answer(broker, int_name)
    broker.logger.info(f"Save broker {broker.id}'s world and store")

### Shutdown Handler ###
async def handle_Shutdown(broker, int_name, int_param, app_param, psk_parse):
    answer(broker, int_name)
    await safe_save(broker)
    broker.logger.info(f"Shut down broker {broker.id}")
    broker.app.shutdown()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks)
    asyncio.get_event_loop().stop()

### Deliver Metadata ###
async def handle_Metadata(broker, int_name, int_param, app_param, psk_parse):
    dataname = psk_parse['dataname']
    response = {}
    # Store metadata
    store_md = broker.store.metadata[dataname] \
        if dataname in broker.store.metadata else Metadata(dataname)
    response['store_md'] = base64.b64encode(pickle.dumps(store_md)).decode()
    # Pub/sub operations metadata
    if dataname in broker.psodb:
        response['pso_info'] = broker.psodb[dataname] 
    # await broker.app.unregister(dataname)   # Disconnets route for old node
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)
    broker.logger.debug(f"Metadata for {dataname} delivered")
