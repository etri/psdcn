from ndn.encoding import Name
from ndn.types import InterestNack, InterestTimeout
from ratelimit import limits, RateLimitException
import asyncio, pickle, base64, random, logging
import sys, datetime
import json

from psdcnv2.utils import *
from psdcnv2.psk import *

### UTILITIES ###
def unparse_cmd(target, proto, dataname, seq=None):
    cmd_str = target + "/" + proto + dataname
    if seq:
        cmd_str += "/" + seq
    return cmd_str

def trim_it(value):
    value = str(value)
    return value[:10] + ("..." if len(value) > 10 else "")

def check_rate(def_rate):
    """
    Look up rate limit value from configuration value "service_rate".
        If the limit value is not defined, use `def_rate` instead.
    """
    rate = config_value("service_rate")
    return int(rate) if rate is not None else def_rate

def answer(broker, int_name, status='OK', value=None, reason=None):
    response = {}
    response['status'] = status
    if value is not None:
        response['value'] = value
    if reason is not None:
        response['reason'] = reason
    broker.app.put_data(int_name,
        content=json.dumps(response).encode(), freshness_period=1)

cmd_infos = {
    PSKCmd.commands["CMD_PA"]: "pubadvinfo",
    PSKCmd.commands["CMD_PU"]: "pubadvinfo",
    PSKCmd.commands["CMD_ST"]: "subinfo",
}
def cmd_info(command):
    return cmd_infos[command] if command in cmd_infos else None

def validate(broker, dataname, servicetoken):
    if broker.validate is False:
        return True
    if dataname == "/test/validation":
        return servicetoken == "hasta la vista"
    return True

### The DISPATCHER ###
async def dispatch(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    # Parse command using the PSK parser
    command = psk_parse['command']
    dataname = psk_parse['dataname']
    app_param = json.loads(bytes(app_param).decode())
    app_param['rninfo'] = RNInfo(brokername=broker.id)
    # broker.logger.debug(f"{broker.id} Dispatch {Name.to_str(int_name)} with {app_param}")

    try:
        # Reflect PA and PU command to psodb
        if command == PSKCmd.commands["CMD_PA"] and dataname not in broker.psodb:
            # Check if client wanted private storage rather than the broker storage
            pubadvinfo = app_param['pubadvinfo']
            where = pubadvinfo['storagetype'] if pubadvinfo['storagetype'] else StorageType.BROKER
            if where == StorageType.BROKER:
                # Handle bundling information
                bundle = pubadvinfo['bundle']
                if bool(bundle) and 'bundlesize' in pubadvinfo:
                    bundlesize = int(pubadvinfo['bundlesize'])
                    if bundlesize < 2:
                        broker.logger.info(f"Bundle size {bundlesize} ignored for {dataname}")
                        pubadvinfo['bundle'] = False
                        del pubadvinfo['bundlesize']
                    else:
                        broker.logger.debug(f"Bundle data {dataname} size {bundlesize}")
                        pass
                broker.logger.debug(f"Broker {broker.id} manages {dataname}")
            else:       # elif where == StorageType.PUBLISHER:
                prefix = param_value(app_param, "pubadvinfo", "pubprefix")
                pubadvinfo['prefix'] = prefix
                pubadvinfo['dataname'] = dataname
                app_param['pubadvinfo'] = pubadvinfo
                broker.logger.debug(f"Publisher {prefix} manages {dataname}")
            # Add advertisement info to PSO database
            broker.psodb.pubadv(dataname, pubadvinfo)
        elif command == PSKCmd.commands["CMD_PU"] and dataname in broker.psodb:
            broker.psodb.pubunadv(dataname)
            broker.store.delete(dataname)
            broker.logger.debug(f"{broker.id} won't manage {dataname} any more")

        # Check scope of operation for commands PA, PU, and ST
        scope = TopicScope.GLOBAL
        command_info = cmd_info(command)
        if command_info is not None:
            user_scope = param_value(app_param, cmd_infos[command], 'topicscope')
            if user_scope:
                scope = int(user_scope)

        # Useful defaults
        success = True
        apq_param = json.dumps(app_param).encode()

        # Check if the request can be processed immediately
        target = arbit(dataname, broker.network)
        if target == broker.id or command == PSKCmd.commands["CMD_PD"] or scope == TopicScope.LOCAL:
            if scope == TopicScope.LOCAL:
                broker.logger.debug(f"Command {command} processed by Data-RN {broker.id}")
            await eval("handle_"+command)(
                broker, int_name, int_param, apq_param, raw_packet, psk_parse)
        else:   # Or, forward the request to target RN
            broker.logger.debug(f"Forward {command} {dataname} from {broker.id} to {target}")
            _, _, content = await broker.app.express_interest(
                Name.from_str(unparse_cmd(target, command, dataname, psk_parse['seq'])),
                interest_param=int_param, app_param=apq_param,
                raw_packet=raw_packet)
    except (InterestTimeout, RateLimitException) as e:
        success = False
        reason = f"** {type(e).__name__} for {command} {dataname} {target}"
    except InterestNack as e:
        success = False
        reason = f"** InterestNack {e.reason} for {command} {dataname} {target}"
    # except Exception as e:
    #     success = False
    #     reason = f"** {type(e).__name__} {str(e)}"
    finally:
        try:
            if success:
                # Just put `content` which has the value to be delivered
                broker.app.put_data(int_name, content=content, freshness_period=1)
            else:
                answer(broker, int_name, status='ERR', reason=reason)
                broker.logger.error(reason)
        except:
            pass


### PUB/SUB HANDLERS ###

### PUBADV (PA) Handler ###
async def handle_PA(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    ini_param = app_param
    app_param = json.loads(bytes(app_param).decode())
    rn_name = param_value(app_param, 'rninfo', 'brokername')
    redefine = param_value(app_param, 'pubadvinfo', 'redefine')
    pub_moved = param_value(app_param, 'pubadvinfo', 'pub_moved')
    dataname = psk_parse['dataname']
    response = {}
    response['new_rn'] = rn_name

    # Chek if dataname was already advertised before
    if dataname in broker.names:
        response['old_rn'] = broker.names[dataname].rn_name
        if bool(redefine) or pub_moved is not None:
            broker.names.advertise(rn_name, dataname)
            response['status'] = "OK"
            action = "redefined"
        else:
            response['status'] = "ERR"
            response['reason'] = "Redefine"
            action = "declined"
    else:
        broker.names.advertise(rn_name, dataname)
        response['status'] = "OK"
        action = "advertised"

    # Check if client wanted self storage rather than the broker storage
    pubadvinfo = app_param['pubadvinfo']
    if 'prefix' in pubadvinfo:
        prefix = pubadvinfo['prefix']
        broker.names[dataname].pubprefix = prefix
        response['prefix'] = prefix
        rn_name = prefix

    # Also register pubadvinfo to information registry
    # Must consider errors...
    reg_cmd, reg_int, reg_app = broker.keeper.make_irreg_cmd(broker.ir_prefix, dataname,
        rawpacket=base64.b64encode(raw_packet))
    reg_app = json.loads(reg_app.decode())
    reg_app['pubadvinfo'] = pubadvinfo
    try:
        await broker.app.express_interest(Name.from_str(reg_cmd),
            app_param=json.dumps(reg_app).encode())
        broker.logger.debug(f"IR registered pubadvinfo for {dataname}")
    except Exception as e:
        #response['status'] = "ERR"
        #response['reason'] = "IRfailure"
        #response = json.dumps(response).encode()
        #broker.app.put_data(int_name, content=response, freshness_period=1)
        #broker.logger.info(f"PA couldn't register {dataname} to IR")
        #return
        pass

    # All done
    broker.logger.info(f"PA {broker.id} {action} {dataname}@{rn_name}")
    response['broker'] = broker.id
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)

### PUBUNADV (PU) Handler ###
async def handle_PU(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    dataname = psk_parse['dataname']
    response = {}
    response['broker'] = broker.id

    # First, unregister from Names
    if dataname not in broker.names:
        response['status'] = "ERR"
        response['reason'] = "Undefined"
        broker.logger.info(f"PU {dataname} undefined at {broker.id}")
    else:
        broker.names.unadvertise(dataname)
        num_names = broker.names.count()
        broker.logger.info(f"PU {dataname} from {broker.id} ({num_names} entries)")
        response['status'] = "OK"

    # Also unregister from the marketplace
    # Must consider errors...
    del_cmd, del_int, del_app = broker.keeper.make_irdel_cmd(broker.ir_prefix, dataname,
        rawpacket=b'')
    try:
        await broker.app.express_interest(Name.from_str(del_cmd))
        broker.logger.debug(f"IR unregistered {dataname}")
    except Exception as e:
        response['status'] = "ERR"
        response['reason'] = "IRfailure"
        response = json.dumps(response).encode()
        broker.app.put_data(int_name, content=response, freshness_period=1)
        broker.logger.info(f"PU couldn't unregister {dataname} from IR")
        return

    # Return response
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)

### PUBDATA (PD) Handler ###
async def handle_PD(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    dataname = psk_parse['dataname']

    ### Mobility stuff
    if dataname not in broker.psodb:
        broker.logger.debug(f"{dataname} new to {broker.id}. Pub moved?")
        # Publisher moved to a new broker!
        # (Re)Advertise dataname to reflect the new Data-RN name
        topic_rn = arbit(dataname, broker.network)
        success = True
        pubadvinfo_m = PubAdvInfo(dataname=dataname)
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
                broker.logger.debug(f"PD.RA {dataname} from {old_rn} to {new_rn}")
                # Fetch PSO and storage metadata from the original Data-RN
                command, int_param, apq_param = \
                    broker.keeper.make_generic_cmd("PsoSmd", prefix=old_rn, dataname=dataname)
                _, _, content = \
                    await broker.app.express_interest(Name.from_str(command),
                        interest_param=int_param, app_param=apq_param, must_be_fresh=True)
                content = json.loads(bytes(content).decode())
                if 'pso_info' in content:
                    pubadvinfo_m = content['pso_info']
                    store_md = pickle.loads(base64.b64decode(content['store_md'].encode()))
                    broker.store.metadata[dataname] = store_md
                    broker.logger.debug(
                        f"{dataname}'s PSO and Store MD copied from {old_rn} to {new_rn}")
            else:
                success = False
        else:
            broker.logger.debug(f"PD.PA {dataname} to {broker.id}")
            broker.names.advertise(broker.id, dataname)
        if success:
            broker.psodb.pubadv(dataname, pubadvinfo_m)
        else:
            reason = f"{dataname} not advertised yet."
            answer(broker, int_name, status='ERR', reason=reason)
            broker.logger.info(f"Publication failed. {reason}")
            return
    ### End mobility stuff

    ### Reject publication for publisher managed store
    pubadvinfo = broker.psodb[dataname]
    if 'prefix' in pubadvinfo:
        prefix = pubadvinfo['prefix']
        if prefix != broker.id:
            reason = f"Publish to {prefix} instead."
        broker.logger.info(f"Publication to {broker.id} failed. {reason}")
        answer(broker, int_name, status='ERR', reason=reason)
        return

    # Gather data items for publication
    app_param = json.loads(app_param.decode())
    seq = int(psk_parse['seq'])
    pub_data = param_value(app_param, 'pubdatainfo', 'data')
    if pub_data is None:        # Large data
        publisher = param_value(app_param, 'pubdatainfo', 'prefix')
        seq1 = seq
        seq2 = int(param_value(app_param, 'pubdatainfo', 'data_eseq'))
        seqs = list(range(seq1, seq2+1))
        vals = []
        apq_param = json.dumps(app_param).encode()
        for pseq in range(seq1, seq2+1):
            command = Name.from_str(publisher + dataname + "/" + str(pseq))
            try:
                _, _, content = await broker.app.express_interest(command,
                    interest_param=int_param, app_param=apq_param, lifetime=10000)
                vals.append(bytes(content).decode())
            except Exception as e:
                broker.logger.error(f"** {type(e).__name__} {str(e)}")
                break
            finally:
                pass
        svs = list(zip(seqs, vals))
    else:                       # Small data (one data item)
        svs = [(seq, pub_data)]

    # Data items ready. Put them in the Store.
    for pseq, pval in svs:
        pso = broker.psodb[dataname]
        pos = broker.store.set(dataname, pval, pseq, pso)
        # assert pub_data == broker.store.get(dataname, 0)
        broker.logger.info(f"PD {trim_it(pval)} to {dataname}[{pos}]@{broker.id}")
        # See if there are pending interests and process them
        response = json.dumps({'status': 'OK', 'value': pval}).encode()
        for pending in broker.pending_interests[:]:
            data_name, seq_no, pint_name, expires = pending
            if dataname == data_name and pos == int(seq_no):
                broker.app.put_data(pint_name, content=response, freshness_period=1)
                broker.pending_interests.remove(pending)
                broker.logger.debug(f"PD.PI {trim_it(pub_data)} to {dataname}[{pos}]@{broker.id}")

    # Report number of data items published
    answer(broker, int_name, value=len(svs))
# End handle_PD

### SUBTOPIC (ST) Handler ###
@limits(calls=check_rate(100)*100, period=100)
async def handle_ST(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    topicname = psk_parse['dataname']
    app_param = json.loads(bytes(app_param).decode())
    matches = [(slot.rn_name if not hasattr(slot, 'pubprefix') else slot.pubprefix, slot.dataname)
        for slot in broker.names.matches(topicname)]
    valid_m = []
    servicetoken = param_value(app_param, 'subinfo', 'servicetoken')
    for match in matches:
        if validate(broker, match[1], servicetoken):
            valid_m.append(match)
        else:
            broker.logger.debug(f"{match[1]} service token validation error")
    broker.logger.info(f"ST {topicname} found {len(valid_m)} matches at {broker.id}")
    answer(broker, int_name, value=valid_m)

### SUBMANI (SM) Handler ###
async def handle_SM(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    dataname = psk_parse['dataname']
    response = {}
    if dataname in broker.store:
        md = broker.store.metadata[dataname]
        response['status'] = "OK"
        response['fst'] = md.fst
        response['lst'] = md.lst
        if md.bun is not None:
            response['bundle_count'] = md.bun.count
            response['bundle_size'] = md.bun.size
        broker.logger.info(f"SM {dataname} served at {broker.id}")
    else:
        response['status'] = "NOT_FOUND"
        broker.logger.info(f"SM {dataname} not found at {broker.id}")
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)

### SUBDATA (SD) Handler ###
async def handle_SD(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    dataname = psk_parse['dataname']
    seq = int(psk_parse['seq'])
    app_param = json.loads(bytes(app_param).decode())
    # Handle get bundle request
    if bool(param_value(app_param, 'subinfo', 'is_bundled')):
        part = "bundle "
        if seq < 1:
            broker.logger.info(f"SD {part}{dataname}[{seq}] failed at {broker.id}")
            answer(broker, int_name, status='ERR', reason='Non-positive bundle number')
            return
        bundle = broker.store.get_bundle(dataname, seq)
        if bundle is None:
            broker.logger.info(f"SD {part}{dataname}[{seq}] failed at {broker.id}")
            answer(broker, int_name, status='ERR', reason=f'Bundle {seq} not found')
            return
        fetched = [value.decode() for value in bundle]
    else:
        part = ""
        fetched = broker.store.get(dataname, seq)
    if fetched is not None:
        answer(broker, int_name, value=fetched)
        broker.logger.info(f"SD {part}{dataname}[{seq}] served at {broker.id}")
    elif int(seq) > 0:
        # Add to broker pending interest table with timestamp
        lifetime = int(int_param.lifetime)
        timestamp = datetime.datetime.now()
        utc_time = timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
        expires = utc_time + lifetime / 1000
        broker.pending_interests.append((dataname, seq, int_name, expires))
        broker.logger.debug(f"SD.PI {dataname}[{seq}] expires at {int(expires)}")
    else:
        answer(broker, int_name, value=None)
        broker.logger.info(f"SD {dataname}[{seq}] failed at {broker.id}")


### ADMIN COMMAND HANDLERS ###

### Status Handler ###
async def handle_Status(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    def time_alive(start):
        format = '%Y-%m-%d %H:%M:%S.%f'
        diff = datetime.datetime.strptime(str(datetime.datetime.now()), format) - \
           datetime.datetime.strptime(str(start), format)
        alive = ""
        days = diff.days; seconds = diff.seconds
        if days > 0: alive += str(days) + "D"
        hours = seconds // 3600 - diff.days * 24
        if hours > 0: alive += str(hours) + "h"
        minutes = seconds // 60 - hours * 60
        if minutes > 0: alive += str(minutes) + "m"
        seconds = seconds % 60
        if seconds > 0: alive += str(seconds) + "s"
        return alive
    response = {}
    response['broker_id'] = broker.id
    response['time_alive'] = time_alive(broker.epoch)
    advs = list(broker.names.names()); advc = len(advs)
    if advc > 5:
        advs = advs[:5]; advs.append("...")
    response['advertised'] = advs, advc
    pubs = list(broker.store.names()); pubc = len(pubs)
    if pubc > 5:
        pubs = pubs[:5]; pubs.append("...")
    response['published'] = pubs, pubc
    response['names'] = type(broker.names).__name__
    response['storage'] = broker.store.media()
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)

### Network Handler ###
async def handle_Network(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    app_param = json.loads(bytes(app_param).decode())
    rn_names = list(param_value(app_param, 'rninfo', 'brokername'))
    broker.network = rn_names
    answer(broker, int_name)
    broker.logger.info(f"Broker {broker.id}'s network set to {rn_names}")

### Save Handler ###
async def handle_Save(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    await broker.save_world(periodic=False)
    await broker.store.flush(periodic=False)
    answer(broker, int_name)
    broker.logger.info(f"Broker {broker.id}'s world and store saved")

### Shutdown Handler ###
async def handle_Shutdown(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    answer(broker, int_name)
    broker.logger.info(f"Broker {broker.id} shut down")
    broker.app.shutdown()

### Debug Handler ###
async def handle_Debug(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    app_param = json.loads(bytes(app_param).decode())
    debug = bool(app_param['debug'])
    if debug:
        broker.logger.setLevel(logging.DEBUG)
        on_off = 'on'
    else:
        broker.logger.setLevel(eval("logging." + config_value('logger', 'level').upper()))
        on_off = 'off'
    answer(broker, int_name)
    broker.logger.info(f"Broker {broker.id}'s debugging turned {on_off}")


### AUXILIARY COMMAND HANDLERS ###
async def handle_PsoSmd(broker, int_name, int_param, app_param, raw_packet, psk_parse):
    dataname = psk_parse['dataname']
    response = {}
    pso_info = broker.psodb[dataname]
    if pso_info is not None:
        response['pso_info'] = pso_info
        store_md = pickle.dumps(broker.store.metadata[dataname])
        response['store_md'] = base64.b64encode(store_md).decode()
    response = json.dumps(response).encode()
    broker.app.put_data(int_name, content=response, freshness_period=1)
