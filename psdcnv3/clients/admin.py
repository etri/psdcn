from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
from ndn.encoding import Name, InterestParam
import sys, json, uuid
import asyncio as aio

from ..psk import *
from ..utils import segment_fetcher

arg_map = {
    'network/set': ('rninfo', lambda a: RNInfo(brokername=a)),
    'status/report': ('window_size', lambda a: str(a[0]) if len(a) > 0 else None),
}

def patch_arg(cmd, arg):
    if arg is None or cmd not in arg_map:
        return {}
    maker = arg_map[cmd]
    return {maker[0]: maker[1](arg)}

def check_action(cmd):
    csplit = cmd.split("/")
    action = csplit[1] if len(csplit) > 1 else "default"
    return csplit[0].capitalize(), action

async def _handle(app, keeper, cmd, prefix, args=None):
    """
    Invoke broker's internal command `cmd`.capitalize().
    """
    cadmin, action = check_action(cmd)
    patched_args = patch_arg(cmd, args)
    if cadmin == "Status":
        return await handle_status(app, keeper, prefix, action, patched_args)
    command, int_param, app_param = \
        keeper.make_generic_cmd(cadmin, prefix, dataname=action, **patched_args)
    data_name, meta_info, content = await app.express_interest(Name.from_str(command),
        interest_param=int_param, app_param=app_param, must_be_fresh=True)
    return bytes(content).decode()

async def handle_status(app, keeper, prefix, action, args):
    command, int_param, app_param = keeper.make_generic_cmd(command="Status",
        dataname=action, prefix=prefix, **args)
    _, _, content = await app.express_interest(Name.from_str(command),
        interest_param=int_param, app_param=app_param)
    reply = json.loads(bytes(content).decode())
    count = int(reply['count'])          # Number of chunks to fetch
    status = bytearray(reply['chunk'].encode())
    if count > 1:
        async for _, _, content, _ in segment_fetcher(app, prefix + "/Status/report", 2, count):
            status.extend(content)
    if len(status) > 0:
        return json.dumps(eval(status.decode()), indent=2)
    return "{}"

async def handle(app, keeper, cmd, prefix, args=None):
    print(await _handle(app, keeper, cmd, prefix, args))
    app.shutdown()

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 admin <broker> [<command>]")
        sys.exit(1)
    app = NDNApp()
    keeper = PSKCmd(app)
    prefix, cmd = sys.argv[1:3]
    args = sys.argv[3:]
    try:
        app.run_forever(after_start=handle(app, keeper, cmd, prefix, args))
    except (InterestNack, InterestTimeout):
        print(f"Broker {prefix} unreachable or timeout")
    except Exception as e:
        print(f"{type(e).__name__} {str(e)}")
    finally:
        pass
