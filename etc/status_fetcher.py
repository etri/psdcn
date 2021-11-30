from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
from ndn.encoding import Name, InterestParam
from ndn.utils import gen_nonce
import json, sys

CMD_ACTION = "/Status/report"

def make_status_command(prefix, window_size):
    command = prefix + CMD_ACTION
    i_param = InterestParam()
    i_param.must_be_fresh = True
    i_param.nonce = gen_nonce()
    i_param.lifetime = 10000            # 10 seconds
    app_param = bytes(json.dumps({'window_size': window_size}), "utf-8")
    return command, i_param, app_param

async def fetch_status(app, prefix, window_size):
    command, interest_param, app_param = make_status_command(prefix, window_size)
    _, _, content = await app.express_interest(Name.from_str(command),
        interest_param=interest_param, app_param=app_param)
    hint = json.loads(bytes(content).decode())
    count = int(hint['count'])          # Number of chunks to fetch
    chunks = [hint['chunk']]            # ADDED
    for seq in range(1, count):         # MODIFIED from range(count) to range(1, count)
        command = Name.from_str(prefix + CMD_ACTION + "/" + str(seq+1))
        try:
            _, _, content = await app.express_interest(command,
                interest_param=interest_param, lifetime=10000)
            chunks.append(bytes(content).decode())
        except Exception as e:
            print(f"** {type(e).__name__} {str(e)}")
            break
        finally:
            pass
    print(''.join(chunks))
    app.shutdown()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 status <broker>")
        sys.exit(1)
    app = NDNApp()
    broker = sys.argv[1]
    try:
        app.run_forever(after_start=fetch_status(app, broker, 5))
    except (InterestNack, InterestTimeout):
        print(f"Broker {broker} unreachable or timeout")
    except Exception as e:
        print(f"{type(e).__name__} {str(e)}")
    finally:
        app.shutdown()

if __name__ == "__main__":
    main()
