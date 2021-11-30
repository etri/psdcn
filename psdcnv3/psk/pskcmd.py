"""
PSK interface for PSDCNv3.
These interfaces are to make commands for publisher, subscriber, broker and IR.
"""
from typing import Any, List, Dict
import urllib.parse

from ndn.encoding import Name, InterestParam
from ndn.utils import gen_nonce

from psdcnv3.psk.pskinfo import *
from psdcnv3.utils import config_value

"""
Interest lifetimes
"""
INT_LT_1 = 1000
INT_LT_4 = 4000
INT_LT_10 = 10000
INT_LT_100 = 100000
INT_LT_1000 = 1000000

def make_int_param():
    int_param = InterestParam(must_be_fresh=True)
    int_param.nonce = gen_nonce()
    int_param.lifetime = INT_LT_10
    return int_param

def make_app_param(app_param):
    return bytes(json.dumps(app_param), 'utf-8')

class PSKCmd(object): 
    commands = {
        # Pub/Sub commands
        "CMD_PA": "PA", "CMD_PU": "PU", "CMD_PD": "PD",
        "CMD_ST": "ST", "CMD_SM": "SM", "CMD_SL": "SL",
        "CMD_MR": "MR", "CMD_MM": "MM", "CMD_MD": "MD",
        "CMD_DB": "DB", 
        # Admin commands
        "CMD_Network": "Network",
        "CMD_Status": "Status",
        "CMD_Shutdown": "Shutdown",
        "CMD_Save": "Save",
        "CMD_Metadata": "Metadata",
    }

    """
    Create a PSKCmd object. PSKCmd object provides interface for making Pub/Sub command name.
    """
    def __init__(self, app, node_name=None, id=None):
        self.app = app
        svc_name = config_value("network_prefix")
        self.svc_name = svc_name if svc_name is not None else "/etri/rn"
        self.node_name = node_name if node_name is not None else config_value("broker_prefix")
        self.id = id if id is not None else self.node_name

    def bootstrap(self) -> None:
        """
        Bootstrap Function
        :param id: id
        :type id: str
        :return: none 
        """
        # TODO: make logic for bootstrap func
        pass

        return

    def parse_command(self, name) -> Dict:
        """
        parse command from name part of packet
        :param name: name part of packet
        :type name: FormalName
        :return: Dict {(command, dataname, seq}
        """
        # assume following name
        # /prefix/opcode/dataname/params-sha256

        # convert FormalName to NonStrictName
        str_name = Name.to_str(name)
        # remove params-sha256 for Application Parameter
        oname = str_name.split("/params-sha256")[0]
        # split name part
        parts = oname.split("/")[1:]
        # check prefix
        command = "ERROR"
        cmd_list = list(PSKCmd.commands.values())
        if Name.is_prefix(self.svc_name, oname):
            prefix = self.svc_name
            nname_cnt = len(self.svc_name.split('/')[1:])
            if parts[nname_cnt] in cmd_list:
                command = parts[nname_cnt]
                d_begin = nname_cnt + 1
            else:
                command = parts[1]
                d_begin = 2
        elif Name.is_prefix(self.node_name, oname): 
            prefix = self.node_name
            bname_cnt = len(self.node_name.split('/')[1:])
            if parts[bname_cnt] in list(PSKCmd.commands.values()):
                command = parts[bname_cnt]
                d_begin = bname_cnt + 1
            else:
                command = parts[1]
                d_begin = 2
        seq = None
        wseq = 0
        # last index is sequence no.
        lastpart = parts[len(parts)-1]
        if command == PSKCmd.commands["CMD_PD"] or \
                command == PSKCmd.commands["CMD_Status"] and lastpart.isdecimal():
            seq = lastpart
            wseq = 1

        # make dataname
        datas = parts[d_begin:(len(parts)-wseq)]
        dataname = "/" + "/".join(datas)
        # replace %xx escapes by their single-character equivalent
        udataname = urllib.parse.unquote(dataname)
        # if seq is Null, OK?
        return {"prefix": prefix, "command": command, "dataname": udataname, "seq": seq}

    def make_generic_cmd(self, command:str, prefix:str, dataname:str="/_", seq:int=None,
                        **kwargs) -> (str, Any):
        """
        make generic command
        :param prefix: network_prefix or broker_prefix
        :type prefix: str
        :param dataname: dataname for publishing data
        :type dataname: str
        :return: command, interest_param, app_param
        """
        if dataname[0] != '/':
            dataname = "/" + dataname
        command = prefix + "/" + command + dataname
        if seq is not None:
            command += "/" + str(seq)
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(**kwargs))
        return command, int_param, app_param

    def make_pubadv_cmd(self, prefix:str, dataname:str, pubadvinfo:PubAdvInfo=None,
                        irinfo:IRInfo=None, rninfo:RNInfo=None) -> (str, Any):
        """
        make pubadv command
        :param prefix: network_prefix or broker_prefix
        :type prefix: str
        :param dataname: dataname for publishing data
        :type dataname: str
        :param pubinfo: pubadvinfo
        :type pubinfo: PubAdvInfo
        :param irinfo: irinfo
        :type irinfo: IRInfo
        :param rninfo: rninfo
        :type rninfo: RNInfo
        :return: command, interest_param, app_param
        """
        # make a pubadv command name with args
        command = prefix + "/PA" + dataname
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(
                    pubadvinfo=pubadvinfo, irinfo=irinfo, rninfo=rninfo))
        return command, int_param, app_param

    def make_pubunadv_cmd(self, prefix, dataname, pubadvinfo:PubAdvInfo=None) -> (str, Any):
        """
        make pubunadv command
        :param prefix: network_prefix or broker_prefix
        :type prefix: str
        :param dataname: dataname for unpublishing data
        :type dataname: str
        :param pubadvinfo: pub information
        :type pubadvinfo: 
        :return: command, interest_param, app_param
        """
        # make a pubunadv command name with args
        command = prefix + "/PU" + dataname
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(pubadvinfo=pubadvinfo))
        return command, int_param, app_param

    def make_pubdata_cmd(self, prefix, dataname, seq, pubdatainfo:PubDataInfo=None) -> (str, Any):
        """
        make pubdata command
        :param prefix: network_prefix
        :type prefix: str
        :param dataname: dataname for publishing data
        :type dataname: str
        :param seq: sequence no.
        :type seq: int
        :param pubed_data: pubed data
        :type pubed_data: any
        :return: command, interest_param, app_param
        """
        # make a pubdata command name with args
        command = prefix + "/PD" + dataname + '/' + str(seq)
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(pubdatainfo=pubdatainfo))
        return command, int_param, app_param

    def make_subtopic_cmd(self, prefix, dataname, local=False, subinfo:SubInfo=None) -> (str, Any):
        """
        make subtopic command
        :param prefix: network_prefix or topicrn_prefix
        :type prefix: str
        :param dataname: topic name
        :type dataname: str
        :param subinfo: subscription information
        :type subinfo: SubInfo
        :return: command, interest_param, app_param
        """
        # make a subtopic command name with args
        command = prefix + ("/SL" if local else "/ST") + dataname
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(subinfo=subinfo))
        return command, int_param, app_param

    def make_submani_cmd(self, dataname, forward_to) -> (str, Any):
        """
        make submani command
        :param dataname: topic name
        :type dataname: str
        :param forward_to: data_rn prefix
        :type forward_to: str
        :return: command, interest_param, app_param
        """
        # make a submani command name with args
        command = self.svc_name + "/SM" + dataname
        int_param = make_int_param()
        int_param.forwarding_hint = [(1, forward_to)]
        return command, int_param, None

    def make_subdata_cmd(self, dataname, seq, forward_to, lifetime=None):
        """
        make subdata command
        :param dataname: topic name
        :type dataname: str
        :param seq: sequence number
        :type seq: int
        :param forward_to: data_rn prefix
        :type forward_to: str
        :param lifetime: interest lifetime in miliseconds
        :type seq: int
        :return: Interest of (command, interest_param, None)
        """
        # make a data request
        command = dataname + "/" + str(seq)
        int_param = make_int_param()
        int_param.must_be_fresh = False # Should be the opposite of pubdata
        int_param.can_be_prefix = True  # Caching for dual CS enablement
        int_param.forwarding_hint = [(0, forward_to)]
        if lifetime:
            int_param.lifetime = lifetime
        # else lifetime defaults to INT_LT_10
        return command, int_param, None

    def make_irreg_cmd(self, prefix, dataname) -> str:
        """
        make irreg command
        :param prefix: ir_prefix
        :type prefix: str
        :param dataname: dataname
        :type dataname: str
        :param packet: raw interest packet
        :type bytes: 
        :return: command, interest_param, app_parm(None)
        """
        # make a irreg command name with args
        command = prefix + "/" + PSKCmd.commands["CMD_MR"] + dataname
        return command, make_int_param(), None

    def make_irmod_cmd(self, prefix, dataname) -> str:
        """
        make irmod command
        :param prefix: ir_prefix
        :type prefix: str
        :param dataname: dataname
        :type dataname: str
        :param packet: raw interest packet
        :type bytes: 
        :return: command, interest_param, app_parm(None)
        """
        # make a irmod command name with args
        command = prefix + "/" + PSKCmd.commands["CMD_MM"] + dataname
        return command, make_int_param(), None

    def make_irdel_cmd(self, prefix, dataname) -> str:
        """
        make irdel command
        :param prefix: ir_prefix
        :type prefix: str
        :param dataname: dataname
        :type dataname: str
        :param packet: raw interest packet
        :type bytes: 
        :return: command, interest_param, app_parm(None)
        """
        # make a irmod command name with args
        command = prefix + "/" + PSKCmd.commands["CMD_MD"] + dataname
        return command, make_int_param(), None

# TODO:
    def make_bakdifs_cmd(self, prefix, dataname, raw_packet) -> (str, Any):
        pass
