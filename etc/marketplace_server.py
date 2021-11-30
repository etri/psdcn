from ndn.app import NDNApp
from ndn.encoding import Name
from ndn.encoding.ndn_format_0_3 import parse_interest
from urllib import parse
import json, base64

# Info Registry
IR = {}
commands = {
    'MR': 'Register',
    'MM': 'Modify',
    'MD': 'Unregister',
}
params_str = '/params-sha256='

def on_interest(name, param, app_param):
    # Delete sha256 part of name
    str_name = Name.to_str(name)
    if params_str in str_name:
        str_name = str_name[:str_name.index(params_str)]
    str_name = parse.unquote(str_name)
    # Determine command and dataname
    command = None
    for cmd in commands.keys():
        if cmd in str_name:
            command = commands[cmd]
            break
    dataname = "/" + ("/".join(str_name.split("/")[4:]))
    # Extract advinfo/data_rn/packet if they are delivered in app_param
    topic_rn = None
    data_rn = None
    advinfo = None
    packet_ = None
    if app_param is not None:
        app_param = json.loads(bytes(app_param).decode())
        pubadvinfo = app_param['advinfo']
        # "topicscope is 0" means GLOBAL while 1 means LOCAL
        topic_rn = app_param['topic_rn']
        data_rn = app_param['data_rn']
        # Check if the name was redefined
        if dataname in IR and not pubadvinfo['redefine']:
            app.put_data(name, content=dataname.encode(), freshness_period=1)
            return
        advinfo = json.dumps(pubadvinfo, indent=2)
        packet_ = app_param['packet_']
    # Show command, and also advinfo/data_rn they were delivered
    print(f">>> {command} {dataname}")
    if cmd == "MR" or cmd == "MM":
        print('AdvInfo:')
        print(advinfo)
        print('Topic-RN:', topic_rn)
        print('Data-RN:', data_rn)
        packet_ = base64.b64decode(packet_)
        formal_name, int_param, binary_str, signature_ptrs = parse_interest(packet_)
        print('Packet:')
        print('{')
        print(f'  "formal_name": {Name.to_str(formal_name)}')
        sig_info = signature_ptrs.signature_info
        if sig_info is not None:
            sig_type = sig_info.signature_type
            key_locator = Name.to_str(sig_info.key_locator.name)
            print(f'  "signature_info": signature_type={sig_type}, key_locator={key_locator}')
        print('}')
        IR[dataname] = data_rn, advinfo, packet_
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
