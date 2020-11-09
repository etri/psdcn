# Interactive/Batch PSDCNv2 Testing Tool

from psdcnv2.clients import Pubsub
from psdcnv2.clients.admin import _handle as admin_handler
from psdcnv2.psk import *
from psdcnv2.utils import load_config, config_value
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
import os, sys, asyncio

# Mode of execution
batch = False

# Reusable values
rns = []
brokers = []
rn_name = None
name = None
names = []
bundlesize = 0
topic = None
data = None
seq = None
args = []
debug = True
sys_command = ""

reader = sys.stdin

def i_print(*value):
    print('==', *value)

def e_print(*value):
    print('**', *value)

def i_input(prompt, value):
    if reader == sys.stdin:
        print(f"{prompt}? "); sys.stdout.flush()
    if inp == '':   # User hit just <ENTER>
        return value
    return inp.strip()

def _name(name):
    if name is None:
        return name
    name = name.strip()
    if not name.startswith("/"):
        return "/" + name
    return name

def check_brokers():
    if rns == []:
        e_print("No brokers are available")
        return False
    return True


# Command Handlers

async def status(ps):
    def stat(s):
        s = eval(s)
        r = ""
        r += f"{s['broker_id']} (time_alive={s['time_alive']})"
        advs = s['advertised']
        if int(advs[1]) > 0:
            r += f"\n   Advertised: {advs[1]} items ("
            for adv in advs[0]: r += f"{adv} "
            r = r.rstrip() + ")"
        pubs = s['published']
        if int(pubs[1]) > 0:
            r += f"\n   Published: {pubs[1]} items ("
            for pub in pubs[0]: r += f"{pub} "
            r = r.rstrip() + ")"
        r += f"\n   Names type: {s['names']}"
        r += f"\n   Storage type: {s['storage']}"
        return r
    for rn in rns:
        rn = _name(rn)
        try:
            i_print(stat(await admin_handler(ps.app, ps.keeper, "status", rn)))
        except Exception as e:
            e_print(f"{type(e).__name__} {str(e)}")
        finally:
            pass

async def advertise(ps):
    global names, bundlesize
    if not check_brokers():
        return
    if args != []:
        names = args[0]
        bundlesize = "0" if len(args) == 1 else args[1]
    else:
        names = i_input("Data names (can use ',')", names)
        bundlesize = i_input("Bundle size", bundlesize)
    bundle_size = int(bundlesize)
    is_bundle = bundle_size >= 2
    for name in names.replace(",", " ").split():
        await ps.pubadv(_name(name),
            bundle=is_bundle, bundlesize=(bundle_size if is_bundle else 0))
    if not batch:
        await status(ps)

async def unadvertise(ps):
    global names
    if not check_brokers():
        return
    if args != []:
        names = args
    else:
        inp_names = i_input("Data names (can use ',')", None)
        names = names if inp_names is None else inp_names.replace(",", " ").split()
    for name in names:
        await ps.pubunadv(_name(name))
    if not batch:
        await status(ps)

async def publish_data(ps):
    global name, seq, data
    if not check_brokers():
        return
    if args != []:
        name, seq, data = args[:3]
    else:
        name = _name(i_input("Data name", name))
        seq = i_input("Seq #", seq)
        data = i_input("Data", data)
    seq_value = int(seq)
    await ps.pubdata(name, data, seq_value)
    if not batch:
        await status(ps)

async def match_topic(ps):
    global topic
    if not check_brokers():
        return
    if args != []:
        topic = args[0]
    else:
        topic = _name(i_input("Topic name", topic))
    matches = await ps.subtopic(topic)
    for match in matches:
        i_print(match)

async def data_manifest(ps):
    global rn_name, name
    if not check_brokers():
        return
    if args != []:
        rn_name, name = args[:2]
    else:
        rn_name = _name(i_input("RN name", rn_name))
        name = _name(i_input("Data name", name))
    fst, lst, b_count, b_size = await ps.submani(rn_name, name)
    response = f"Last batch: {fst}-{lst}"
    if b_size > 0:      # Bundled data
        response += f", {b_count} bundles (size {b_size})"
    i_print(response)

async def request_data(ps):
    global rn_name, name, seq
    if not check_brokers():
        return
    if args != []:
        rn_name, name, seq = args[:3]
    else:
        rn_name = _name(i_input("RN name", rn_name))
        name = _name(i_input("Data name", name))
        seq = i_input("Seq #", seq)
    seq_value = int(seq)
    i_print(await ps.subdata(rn_name, name, seq_value))

async def request_bundle(ps):
    global rn_name, name, seq
    if not check_brokers():
        return
    if args != []:
        rn_name, name, seq = args[:3]
    else:
        rn_name = _name(i_input("RN name", rn_name))
        name = _name(i_input("Data name", name))
        seq = i_input("Bundle #", seq)
    seq_value = int(seq)
    i_print(await ps.subdata(rn_name, name, seq_value, is_bundled=True))

async def save(ps):
    global brokers
    if args != []:
        brokers = args
    else:
        inp_bkr = i_input("Brokers (can use ',')", None)
        brokers = brokers if inp_bkr is None else inp_bkr.replace(",", " ").split()
    for broker in brokers:
        await admin_handler(ps.app, ps.keeper, "save", broker.strip())

async def save_world(ps):
    for rn in rns:
        await admin_handler(ps.app, ps.keeper, "save", rn)

async def make_network(ps):
    for rn in rns:
        rn = _name(rn)
        await admin_handler(ps.app, ps.keeper, "network", rn, sorted(rns))

async def set_network(ps):
    global rns, brokers
    if args != []:
        brokers = args
    else:
        inp_bkr = i_input("Brokers (can use ',')", None)
        brokers = brokers if inp_bkr is None else inp_bkr.replace(",", " ").split()
    rns = [_name(broker) for broker in brokers]
    await make_network(ps)
    if not batch:
        await status(ps)

async def debug_mode(ps):
    global debug
    debug = not debug
    for rn in rns:
        await admin_handler(ps.app, ps.keeper, "debug", rn, [debug])
    ps.set_debug_mode(debug)

async def stop(ps):
    global rns, brokers
    if args != []:
        brokers = args
    else:
        inp_bkr = i_input("Brokers (can use ',')", None)
        brokers = brokers if inp_bkr is None else inp_bkr.replace(",", " ").split()
    for broker in brokers:
        broker = _name(broker)
        if broker not in rns:
            e_print(f"{broker} is unknown")
            continue
        await admin_handler(ps.app, ps.keeper, "save", broker)
        await admin_handler(ps.app, ps.keeper, "shutdown", broker)
        rns.remove(broker)
    await make_network(ps)

async def stop_world(ps):
    global rns, args
    args = rns.copy()
    if args != []:
        await stop(ps)
        print(f"Shut down brokers {', '.join(args)}")
    rns = []

async def stop_purge_world(ps):
    await stop_world(ps)
    os.system(f"cd scripts; cleanup")

async def start(ps):
    global rns, brokers
    if args != []:
        brokers = args
    else:
        inp_bkr = i_input("Brokers (can use ',')", None)
        brokers = brokers if inp_bkr is None else inp_bkr.replace(",", " ").split()
    if len(brokers) == 0:
        return
    for broker in brokers:
        broker = _name(broker)
        os.system(f"cd scripts; start-broker {broker}; sleep 1")
        await asyncio.sleep(0.5)
        rns.append(broker)
    await asyncio.sleep(1)
    await make_network(ps)

async def start_world(ps):
    global args, rns
    await stop_world(ps)    # for sure
    # os.system(f"cd scripts; start-world")
    args = config_value("network")
    if args is None:
        args = ["/rn-1", "/rn-2", "/rn-3"]
    rns = []
    await start(ps)

async def leave(ps):
    print("Good bye!")
    ps.app.shutdown()
    await asyncio.sleep(0.5)
    sys.exit(0)

async def stop_and_leave(ps):
    await stop_world(ps)
    await leave(ps)

async def stop_purge_and_leave(ps):
    await stop_purge_world(ps)
    await leave(ps)

async def run_system(ps):
    global sys_command
    if args != []:
        sys_command = ' '.join(args)
    else:
        sys_command = i_input("Enter command", sys_command).strip()
    os.system(sys_command)

async def rerun_system(ps):
    os.system(sys_command)

async def no_action(ps):
    pass

def _command(cmd):
    if cmd in command_map:
        return cmd
    elif cmd in abbrevs:
        return abbrevs[cmd]
    return None

async def help(ps):
    # print("Choose an action\n----------------\n")
    for command in command_map:
        print(f"{command}: {command_map[command][0]}")
    # print("<ENTER>: Redo last command\n")

command_map = {
    'advertise': ("Advertise data names (pa)", advertise),
    'unadvertise': ("Unadvertise data names (pu)", unadvertise),
    'publish': ("Publish data (pd)", publish_data),
    'subscribe': ("Subscribe to a topic (st)", match_topic),
    'manifest': ("Request data manifest (sm)", data_manifest),
    'getdata': ("Request data (sd)", request_data),
    'getbundle': ("Request bundle (sb)", request_bundle),
    'status': ("Inquire brokers' status (info, i)", status),
    'network': ("Set network (n)", set_network),
    'start': ("Start local brokers (s)", start),
    'Start': ("Purge all backups and start /rn-1~3 (S)", start_world),
    'stop': ("Stop given brokers (x)", stop),
    'Stop': ("Stop all running brokers (X)", stop_world),
    'Stop!':("Stop and purge broker backups (XX)", stop_purge_world),
    'save': ("Save given brokers' world (w)", save),
    'Save': ("Save all running brokers' world (W)", save_world),
    'quit': ("Quit without stopping brokers (q)", leave),
    'Quit': ("Stop all running brokers and quit (Q)", stop_and_leave),
    'Quit!':("Stop brokers, purge backups and quit (QQ)", stop_purge_and_leave),
    'debug': ("Toggle logging level to debug (d)", debug_mode),
    'system': ("Run system command (!)", run_system),
    'repeat':("Repeat last system command (!!)", rerun_system),
    'help': ("Help (h, ?)", help),
}
abbrevs = {
    'pa': 'advertise',
    'pu': 'unadvertise',
    'pd': 'publish',
    'st': 'subscribe',
    'sm': 'manifest',
    'sd': 'getdata',
    'sb': 'getbundle',
    'i': 'status',
    'info': 'status',
    'n': 'network',
    's': 'start',
    'S': 'Start',
    'x': 'stop',
    'X': 'Stop',
    'XX': 'Stop!',
    'w': 'save',
    'W': 'Save',
    'q': 'quit',
    'Q': 'Quit',
    'QQ': 'Quit!',
    'd': 'debug',
    'p': 'pause',
    '!': 'system',
    '!!': 'repeat',
    'h': 'help',
    '?': 'help',
}

async def choices():
    global args

    mode = "Batch" if batch else "Interactive"
    print(f"Welcome to {mode} PSDCNv2 Tool!")
    print("Type 'h' or '?' for help")
    print()

    char_cmds = [c for c in command_map.keys()]
    while True:
        try:
            if not batch:
                print(">", end=" "); sys.stdout.flush()
            choose = reader.readline().strip()
            # Support for one-line command
            args = []
            if len(choose) > 0:
                _choose = choose.replace(",", " ").split()
                choose, *args = _choose
                choose = choose.strip()
                if choose == 'pause':
                    print(input("# " + " ".join(args) + "..."))
                    sys.stdout.flush()
                    continue
                if choose[0] == '!' and choose != '!!':
                    args = [choose[1:]] + args
                    choose = '!'
            # Parse command
            choice = _command(choose)
            if choose == '':
                continue            # ignore empty command
            if choice is not None:
                if batch:
                    print(">", choice, *args); sys.stdout.flush()
                # Fire the command
                print(); sys.stdout.flush()
                await command_map[choice][1](ps)
            else:
                print(f"Unknown command! '{choose}'")
        except (InterestNack, InterestTimeout):
            print(f"** Broker unreachable or timeout")
        except Exception as e:
            print(f"** {type(e).__name__}: {str(e)}")
        finally:
            pass
        print(); sys.stdout.flush()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        batch = True
        reader = open(sys.argv[1], 'r')
    app = NDNApp()
    ps = Pubsub(app)
    load_config('psdcnv2.config')
    app.run_forever(after_start=choices())
