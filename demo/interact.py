# Interactive/Batch PSDCNv3 Testing Tool

from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
from ndn.encoding import Name, InterestParam
from ndn.encoding.ndn_format_0_3 import parse_data
from ndn.utils import gen_nonce
import os, sys, asyncio, json

from psdcnv3.clients import Pubsub
from psdcnv3.clients.admin import _handle as admin_handler
from psdcnv3.psk import *
from psdcnv3.utils import load_config, config_value

# Mode of execution
batch = False

# Reusable values
rns = []
rn_name = None
name = None
names = []
topic = None
data = None
seq = None
args = []
given_ = ""
sys_command = ""

reader = sys.stdin

# Reusable methods
def i_print(*value):
    print('=', *value)

def b_print(*value):
    print(' ', *value)

def e_print(*value):
    print('#', *value)

def i_input(prompt, value):
    if reader == sys.stdin:
        print(f"{prompt}? "); sys.stdout.flush()
    inp = input()
    if inp == '':   # User hit just <ENTER>
        return value
    return inp.strip()

def normalize(name):
    if not name:
        return name
    name = name.strip()
    if name[-1] == '/':
        name = name[:-1]
    if not name.startswith("/"):
        return "/" + name
    return name

def check_brokers(ps):
    if rns == []:
        e_print("No brokers available")
        return False
    # Rep broker for this client
    ps.broker = rns[0].strip()
    return True

def fetch_option(option):
    def parse(line, quote):
        return line.partition(quote)[0]
    try:
        value = None
        param = option + '='
        # Throws exception if no such option was provided
        index = next(i for i, v in enumerate(args) if v.startswith(param))
        value = args[index][len(param):]
        if value[0] in ['"', "'"]:
            value = parse(given_[given_.find(param)+len(param)+1:], value[0])
        return value
    except Exception:
        return None


# Command Handlers

# --- PUB/SUB Commands ---

# Advertise/Unadvertise
async def advertise(ps):
    if not check_brokers(ps):
        return
    if len(args) < 1 or len(args) > 2:
        e_print('Usage: ' + usages['pubadv'])
        return
    name = args[0]
    topicscope = TopicScope.LOCAL if '@local' in args else TopicScope.GLOBAL
    redefine = '@redefine' in args
    await ps.pubadv(normalize(name), topicscope=topicscope, redefine=redefine)

async def unadvertise(ps):
    if not check_brokers(ps):
        return
    if len(args) < 1 or len(args) > 2:
        e_print('Usage: ' + usages['pubunadv'])
        return
    name = args[0]
    topicscope = TopicScope.LOCAL if '@local' in args else TopicScope.GLOBAL
    allow_undefined = '@allow_undefined' in args
    await ps.pubunadv(normalize(name), topicscope=topicscope, allow_undefined=allow_undefined)

# Data publications
async def publish_data(ps):
    global name, seq, data
    if seq is None:
        seq = "0"
    if not check_brokers(ps):
        return
    if args != []:
        if len(args) >= 3:
            name, seq = args[:2]
            data = args[2:]
        else:
            e_print('Usage: ' + usages['pubdata'])
            return
    elif name is not None:
        name = normalize(i_input(f"Data name [{name}]", name))
        new = int(seq) + 1
        seq = i_input(f"Seq # [{new}]", str(new))
        data = i_input(f"Data [{data}]", data)
    else:
        e_print('Usage: ' + usages['pubdata'])
        return
    if type(data) == list:
        data = ' '.join(data)
    if seq.isdigit():
        await ps.pubdata(normalize(name), data, int(seq))
    else:
        e_print(f"'{seq}'", 'is an invalid number')
        return
    # if not batch:
    #     await status(ps, with_config=False)

async def set_publisher_prefix(ps):
    """
    Set publisher prefix for the pubsub client
    """
    ps.pub_prefix = normalize(args[0]) if args else None

# Subscribe to a topic
async def do_match_topic(ps, topicscope):
    matcher = ps.subtopic if topicscope == TopicScope.GLOBAL else ps.sublocal
    servicetoken, exclude = fetch_option('@servicetoken'), fetch_option('@exclude')
    options = {'servicetoken': servicetoken, 'exclude': exclude}
    return await matcher(args[0], **options)

async def match_topic(ps):
    if not check_brokers(ps):
        return
    if len(args) < 1:
        e_print('Usage: ' + usages['subtopic'])
        return
    if '@local' in args:
        topicscope = TopicScope.LOCAL
    else:
        topicscope = TopicScope.GLOBAL
    if topicscope == TopicScope.GLOBAL:
        matches = await do_match_topic(ps, topicscope)
        for match in matches.items():
            i_print(match[0], *match[1])
    else:
        rn_name, manifests = await do_match_topic(ps, topicscope)
        if rn_name:
            i_print(f"broker: {rn_name}")
            for (dataname, fst, lst) in manifests:
                b_print(f"{dataname} {fst}-{lst}")

# Data manifest request
async def data_manifest(ps):
    if not check_brokers(ps):
        return
    if len(args) < 2:
        e_print('Usage: ' + usages['submani'])
        return
    dataname, rn_names = args[0], args[1:]
    manifest = None
    for rn_name in rn_names:
        mani = await ps.submani(dataname, rn_name)
        if mani and not ps.reason:
            # if manifest:
            #     mani = (mani[0], mani[1], mani[2])
            i_print(f"{mani[0]} {mani[1]}-{mani[2]}")
            manifest = mani

# Data request
async def get_data(ps):
    """
    Common function for getdata and bookdata commands
    """
    if not check_brokers(ps):
        return
    if len(args) < 3:
        e_print('Usage: ' + usages['subdata'])
        return
    name, seq, f_h = args[:3]
    if not seq.isdigit():
        e_print(f"'{seq}'", 'is an invalid number')
        return
    if len(args) > 3:
        lifetime = args[3]
        if lifetime.isdigit():
            lifetime = int(lifetime)*1000
        else:
            e_print(f"'{lifetime}'", 'is an invalid number')
            return
    else:
        lifetime = None
    content = await ps.subdata(normalize(name), int(seq), f_h, lifetime=lifetime)
    i_print(bytes(content).decode() if content else "None")

# --- ADMIN commands ---
async def status(ps, with_config=False):
    if len(args) > 0:
        with_config = True
    def stat(s):
        s = eval(s)     # Ask admin handler to do the heavy lifting
        config, status = s['config'], s['status']
        r = ""
        r += f"{config['broker_id']}"
        if with_config:
            r += f" (uptime={status['time']['uptime']})"
        advs = status['advertised']
        if int(advs['total']) > 0:
            names = advs['names']
            if len(names) > 0:
                r += f"\n  Advertised {advs['total']} names: "
                for adv in advs['names']: r += f"{adv}, "
                r = r[:-2]      # trim last ", "
            locs = advs['local_names']
            if len(locs) > 0:
                r += f"\n  Advertised {len(locs)} local names: "
                for adv in locs: r += f"{adv}, "
                r = r[:-2]      # trim last ", "
        pubs = status['published']
        if int(pubs['total']) > 0:
            r += f"\n  Published {pubs['total']} items: "
            for pub in pubs['manifest']:
                mani = list(pub.values())
                r += f"{mani[0]} {mani[1]}-{mani[2]}, "
            r = r[:-2]
        if with_config:
            managers = config['managers']
            r += f"\n  Names type: {managers['name_manager']}"
            r += f"\n  Storage type: {managers['storage_manager']}"
        return r
    for rn in rns:
        try:
            i_print(stat(await admin_handler(ps.app, ps.keeper, "status", normalize(rn), 0)))
        except Exception as e:
            e_print(f"\n{type(e).__name__} {str(e)}")
        finally:
            pass

async def save(ps):
    for broker in args:
        await admin_handler(ps.app, ps.keeper, "save", broker.strip())

async def save_world(ps):
    for rn in rns:
        await admin_handler(ps.app, ps.keeper, "save", rn)

async def make_network(ps):
    for rn in rns:
        rn = normalize(rn)
        await admin_handler(ps.app, ps.keeper, "network/set", rn, rns)  # sorted(rns)

async def set_network(ps):
    global rns
    if args != []:
        rns = [normalize(broker) for broker in args]
    ps.broker = rns[0]
    await make_network(ps)
    if not batch:
        await status(ps, with_config=False)

async def set_default_network(ps):
    global args, rns
    args = config_value("network")
    if args is None:
        args = ["/etri/rn-1", "/etri/rn-2", "/etri/rn-3"]
    rns = []
    await set_network(ps)

async def discover_network(ps):
    if not check_brokers(ps):
        return
    brokers = await admin_handler(ps.app, ps.keeper, "network/discover", ps.broker, None)
    i_print(eval(brokers)["brokers"])

async def stop(ps):
    global rns
    for broker in args:
        broker = normalize(broker)
        if broker not in rns:
            e_print(f"{broker} is unknown")
            continue
        await admin_handler(ps.app, ps.keeper, "save", broker)
        await admin_handler(ps.app, ps.keeper, "shutdown", broker)
        rns.remove(broker)
    await make_network(ps)

async def stop_world(ps):
    global args, rns
    args = rns.copy()
    if args != []:
        await stop(ps)
        print(f"Shut down brokers {', '.join(args)}")
    rns = []

async def stop_purge_world(ps):
    await stop_world(ps)
    os.system(f"cd scripts; clean-world")

async def start(ps):
    global rns
    if args == []:
        return
    for broker in args:
        if broker not in rns:
            broker = normalize(broker)
            os.system(f"cd scripts; start-broker {broker}; sleep 1")
            await asyncio.sleep(0.5)
            rns.append(broker)
    await asyncio.sleep(1)
    await make_network(ps)
    await status(ps, with_config=True)

async def start_world(ps):
    global args, rns
    await stop_world(ps)    # for sure
    args = config_value("network")
    if args is None:
        args = ["/etri/rn-1", "/etri/rn-2", "/etri/rn-3"]
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
    sys_command = ' '.join(args)
    os.system(sys_command)

async def rerun_system(ps):
    os.system(sys_command)

async def no_action(ps):
    pass

# Command parser
def _command(cmd):
    if cmd in commands:
        return cmd
    elif cmd in expanded:
        return expanded[cmd]
    return None

def abbrev_str(abbrev):
    if type(abbrev) != list:
        return abbrev
    return ", ".join(abbrev)

async def help(ps):
    for cmd in usage_map:
        print(f"{cmd} (abb: {abbrev_str(usage_map[cmd][1])})\n  {usage_map[cmd][0]}")

usage_map = {
    'pubadv <dataname> [@local] [@redefine]':
        ("Advertise data names.", ["pa", "advertise"], advertise),
    'pubunadv <dataname> [@local] [@allow_undefined]':
        ("Unadvertise data names", ["pu", "unadvertise"], unadvertise),
    'pubdata <dataname> <seq#> <data>':
        ("Publish data", ["pd", "publish"], publish_data),
    'pub_prefix [<prefix>]':
        ("Set or clear publisher prefix", "pp", set_publisher_prefix),
    'subtopic <topic> [@local] [@servicetoken="<token>"] [@exclude="<exclude>"]':
        ("Subscribe to a topic", ["st", "subscribe"], match_topic),
    'submani <dataname> <rn-name>...':
        ("Request data manifest", ["sm", "manifest"], data_manifest),
    'subdata <dataname> <seq#> <forward_to> [<lifetime>]':
        ("Request data (lifetime in sec)", ["sd", "getdata", "gd"], get_data),
    'status [verbose]':
        ("Inquire brokers' status", ["info", "i"], status),
    'network <rn-name>...':
        ("Set network", "n", set_network),
    'Network':
        ("Set network for the default broker network", "N", set_default_network),
    'discover':
        ("Discover network", "di", discover_network),
    'start rn-name':
        ("Start local brokers", "s", start),
    'Start':
        ("Purge all backups and start default broker network", "S", start_world),
    'stop rn-name':
        ("Stop given brokers", "x", stop),
    'Stop':
        ("Stop all running brokers", "X", stop_world),
    'Stop!':
        ("Stop and purge broker backups", "XX", stop_purge_world),
    'save rn-name':
        ("Save given brokers' world", "w", save),
    'Save':
        ("Save all running brokers' world", "W", save_world),
    'quit':
        ("Quit without stopping brokers", "q", leave),
    'Quit':
        ("Stop all running brokers and quit", "Q", stop_and_leave),
    'Quit!':
        ("Stop brokers, purge backups and quit", "QQ", stop_purge_and_leave),
    'system':
        ("Run system command", "!", run_system),
    'repeat':
        ("Repeat last system command", "!!", rerun_system),
    'help':
        ("Show this information", ["h", "?"], help),
}

commands, usages, expanded = {}, {}, {}
for cmd in usage_map:
    command = cmd.split(" ")[0]
    commands[command] = usage_map[cmd][2]
    usages[command] = cmd
    abbrev = usage_map[cmd][1]
    if type(abbrev) == str:
        abbrev = [abbrev]
    for abbr in abbrev:
        expanded[abbr] = command

# The command interpreter loop
NOTICE = '$'
async def choices():
    global given_, args

    mode = "Batch" if batch else "Interactive"
    print(f"Welcome to {mode} PSDCNv3 Tool!")
    if not batch:
        print("Type 'h' or '?' for help")
    print()

    while True:
        try:
            if not batch:
                print(">", end=" "); sys.stdout.flush()
            chosen = reader.readline()
            paused = False
            notice = ''
            if NOTICE  in chosen:
                # Strip notice
                notpos = chosen.index(NOTICE)
                notice = chosen[notpos:].strip()
                chosen = chosen[:notpos]
            chosen = chosen.strip()
            if not chosen:  # The whole line is a blank (or a notice line)
                if batch:
                    print(notice if notice else ""); sys.stdout.flush()
                continue
            given_ = chosen
            # Support for one-line command
            args = []
            if len(chosen) > 0:
                chosen, *args = chosen.replace(",", " ").split()
                chosen = chosen.strip()
                # Direct command or data request
                if chosen[0] == "/":
                    if batch:
                        print(">", chosen, *args, notice); sys.stdout.flush()
                    int_param = InterestParam()
                    int_param.must_be_fresh = True      # !!!
                    int_param.can_be_prefix = True      # Caching for dual CS enablement
                    int_param.nonce = gen_nonce()
                    if len(args) > 0:
                        int_param.forwarding_hint = [(1, normalize(args[0]))]
                    _, _, content = await ps.app.express_interest(
                        Name.from_str(chosen), interest_param=int_param)
                    if any(chosen.startswith(rn_name + "/") for rn_name in rns):
                        # Admin request
                        print(json.dumps(json.loads(bytes(content)), indent=2))
                    else:
                        # PubSub or Data request
                        i_print(str(bytes(content), "utf-8") if content else None); 
                        if not batch:
                            print()
                    sys.stdout.flush()
                    continue
                # Pause
                if chosen == 'pause':
                    paused = True
                    chosen = input(NOTICE + " " + given_[6:] + "...")
                    sys.stdout.flush()
                    continue
                # System commands
                if chosen[0] == '!' and chosen != '!!':
                    args = [chosen[1:]] + args
                    chosen = '!'
            # Parse command
            choice = _command(chosen)
            if chosen == '':
                continue            # ignore empty command
            if choice is not None:
                if batch:
                    print(">", choice, *args, notice); sys.stdout.flush()
                ps.reason = None
                await commands[choice](ps)
                if ps.reason is not None:
                    e_print(ps.reason)
            else:
                e_print(f"Unknown command! '{chosen}'")
        except (InterestNack, InterestTimeout):
            e_print("Name unreachable or timeout")
        except Exception as e:
            e_print(f"{type(e).__name__}: {str(e)}")
        if not batch:
            print(); sys.stdout.flush()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        batch = True
        if sys.argv[1] == "-b":
            reader = sys.stdin
        else:
            reader = open(sys.argv[1], 'r')
    app = NDNApp()
    ps = Pubsub(app)
    load_config('psdcnv3.config')
    app.run_forever(after_start=choices())
