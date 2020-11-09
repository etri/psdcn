from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
from ndn.encoding import Name, InterestParam
import sys, json

from ..psk import *

args_map = {
    'network': ('rninfo', lambda a: RNInfo(brokername=a)),
    'debug': ('debug', lambda a: str(a[0]).upper()[0] == 'T'),
}
def patch_args(cmd, args):
    if args is None or cmd not in args_map:
        return {}
    maker = args_map[cmd]
    return {maker[0]: maker[1](args)}

async def _handle(app, keeper, cmd, prefix, args=None):
    """
    Invoke broker's internal command `cmd`.capitalize().
    """
    command, interest_param, app_param = \
        keeper.make_generic_cmd(cmd.capitalize(), prefix, **patch_args(cmd, args))
    data_name, meta_info, content = await app.express_interest(Name.from_str(command),
        interest_param=interest_param, app_param=app_param, must_be_fresh=True)
    return bytes(content).decode()

async def handle(app, keeper, cmd, prefix, args=None):
    print(await _handle(app, keeper, cmd, prefix, args))
    sys.exit(0)

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
    # except Exception as e:
    #     print(f"{type(e).__name__} {str(e)}")
