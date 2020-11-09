from ndn.app import NDNApp
from ndn.encoding import Name
import json, base64

# Info Registry
IR = {}
commands = {
    'MR': 'Register',
    'MM': 'Modify',
    'MD': 'Unregister',
}

def on_interest(name, param, app_param):
    # Delete sha256 part of name
    str_name = Name.to_str(name)
    params_str = '/params-sha256='
    if params_str in str_name:
        str_name = str_name[:str_name.index(params_str)]
    # Determine command and dataname
    command = None
    for cmd in commands.keys():
        if cmd in str_name:
            command = commands[cmd]
            break
    dataname = "/" + ("/".join(str_name.split("/")[4:]))
    # Extract pubadvinfo and raw_packet if they are delivered in app_param
    pubadvinfo = None
    raw_packet = None
    if app_param is not None:
        app_param = json.loads(bytes(app_param).decode())
        pubadvinfo = json.dumps(app_param['pubadvinfo'], indent=2)
        raw_packet = app_param['rawpacket']
    # Show command, and also pubadvinfo/raw_packet if they were delivered
    print(f">>> {command} {dataname}")
    if cmd == "MR" or cmd == "MM":
        print(pubadvinfo)
        print('Raw packet:', base64.b64decode(raw_packet))
        IR[dataname] = pubadvinfo, raw_packet
        print(f"<<< {command}ed {dataname}")
    elif cmd == "MD":
        if dataname in IR:
            del IR[dataname]
            print(f"<<< {command}ed {dataname}")
        else:
            print(f"<<< {command} failed -- {dataname} not found")
    # Put back dataname as response
    app.put_data(name, content=dataname.encode(), freshness_period=1)
    print(f"Entries are {','.join(list(IR.keys())[-20:])}...")
    print()

async def main(app):
    print("Marketplace Server [Mockup]\n")
    await app.register("/etri/marketplace", on_interest)

if __name__ == '__main__':
    app = NDNApp()
    app.run_forever(after_start=main(app))
