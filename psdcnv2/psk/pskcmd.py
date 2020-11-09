"""
PSK interface for PSDCNv2.
These interfaces are to make Pub/Sub Command for publisher, subscriber, broker and IR.
"""
from typing import Any, List, Dict
import urllib.parse

from ndn.encoding import Name, Component, InterestParam, is_binary_str, BinaryStr
from ndn.utils import gen_nonce

from psdcnv2.psk.pskinfo import *
from psdcnv2.utils import config_value

"""
define Interest lifetime
"""
INT_LT_1 = 1000
INT_LT_4 = 4000
INT_LT_10 = 10000
INT_LT_100 = 100000
INT_LT_1000 = 1000000


class PSKCmd(object): 
    commands = {
        # Pub/Sub commands
        "CMD_PA": "PA", "CMD_PU": "PU", "CMD_PD": "PD",
        "CMD_ST": "ST", "CMD_SM": "SM", "CMD_SD": "SD",
        "CMD_MR": "MR", "CMD_MM": "MM", "CMD_MD": "MD",
        "CMD_DB": "DB",
        # Admin commands
        "CMD_Network": "Network",
        "CMD_Status": "Status",
        "CMD_Shutdown": "Shutdown",
        "CMD_Save": "Save",
        "CMD_Debug": "Debug",
        "CMD_PsoSmd": "PsoSmd",
    }

    """
    Create a PSKCmd object. PSKCmd object provides interface for making Pub/Sub command name.
    """
    def __init__(self, app, bro_name=None, identity=None):
        self.app = app
        self.net_name = config_value("network_prefix")
        if self.net_name is None:
            self.net_name = "/rn"   # Fallback if network_prefix is not defined elsewhere
        if bro_name is not None:
            self.bro_name = bro_name
        else:
            self.bro_name = config_value("broker_prefix")
        if identity is not None:
            self.identity = identity
        else:
            self.identity = self.bro_name

    def bootstrap(self) -> None:
        """
        Bootstrap Function
        :param id: identity
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
        if Name.is_prefix(self.net_name, oname):
            nname_cnt = len(self.net_name.split('/')[1:])
            if parts[nname_cnt] in cmd_list:
                command = parts[nname_cnt]
                d_begin = nname_cnt + 1
            else:
                command = parts[1]
                d_begin = 2
        elif Name.is_prefix(self.bro_name, oname): 
            bname_cnt = len(self.bro_name.split('/')[1:])
            if parts[bname_cnt] in list(PSKCmd.commands.values()):
                command = parts[bname_cnt]
                d_begin = bname_cnt + 1
            else:
                command = parts[1]
                d_begin = 2
        seq = None
        wseq = 0
        # last index is sequence no.
        if command == PSKCmd.commands["CMD_PD"] or command == PSKCmd.commands["CMD_SD"]:
            seq = parts[len(parts)-1]
            wseq = 1
        # make dataname
        datas = parts[d_begin:(len(parts)-wseq)]
        dataname = "/" + "/".join(datas)
        # replace %xx escapes by their single-character equivalent
        udataname = urllib.parse.unquote(dataname)
        # if seq is Null, OK?
        return {"command": command, "dataname": udataname, "seq": seq}

    def make_generic_cmd(self, command:str, prefix:str, dataname:str="/_",
                        pubadvinfo:PubAdvInfo=None,
                        irinfo:IRInfo=None, rninfo:RNInfo=None, **kwargs) -> (str, Any):
        """
        make generic command
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
        command = prefix + "/" + command + dataname
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_10
        param = PSKParameters(pubadvinfo=pubadvinfo, irinfo=irinfo, rninfo=rninfo, **kwargs)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

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
        #command = Name.to_str(prefix + "/" + CMD_PUBADV + dataname)
        command = prefix + "/" + PSKCmd.commands["CMD_PA"] + dataname
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_10
        param = PSKParameters(pubadvinfo=pubadvinfo, irinfo=irinfo, rninfo=rninfo)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

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
        command = prefix + "/" + PSKCmd.commands["CMD_PU"] + dataname
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_10
        param = PSKParameters(pubadvinfo=pubadvinfo)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

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
        command = prefix + "/" + PSKCmd.commands["CMD_PD"] + dataname + '/' + str(seq)
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_4
        param = PSKParameters(pubdatainfo=pubdatainfo)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

    def make_subtopic_cmd(self, prefix, dataname, subinfo:SubInfo=None) -> (str, Any):
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
        command = prefix + "/" + PSKCmd.commands["CMD_ST"] + dataname
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_10
        # make a app_params for subscription
        param = PSKParameters(subinfo=subinfo)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

    def make_submani_cmd(self, prefix, dataname) -> (str, Any):
        """
        make submani command
        :param prefix: network_prefix or topicrn_prefix
        :type prefix: str
        :param dataname: topic name
        :type dataname: str
        :return: command, interest_param, app_param
        """
        # make a submani command name with args
        command = prefix + "/" + PSKCmd.commands["CMD_SM"] + dataname
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_10
        # make a app_params for subscription
        param = PSKParameters()
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

    def make_subdata_cmd(self, prefix, dataname, seq, lifetime=None,
                         subinfo:SubInfo=None) -> (str, Any):
        """
        make subdata command
        :param prefix: datarn_prefix
        :type prefix: str
        :param dataname: dataname
        :type dataname: str
        :param seq: sequence no.
        :type seq: int
        :param subinfo: subinfo
        :type subinfo: SubInfo
        :return: command, interest_param, app_param
        """
        # make a subdatareq command name with args
        #command = Name.to_str(prefix + "/" + CMD_SUBDATAREQ + dataname + f'/{seq:d}')
        command = prefix + "/" + PSKCmd.commands["CMD_SD"] + dataname + "/" + str(seq)
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = (lifetime if lifetime else INT_LT_10)
        # make a app_params for subscription
        param = PSKParameters(subinfo=subinfo)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

    def make_irreg_cmd(self, prefix, dataname, rawpacket:BinaryStr=None) -> (str, Any):
        """
        make irreg command
        :param prefix: ir_prefix
        :type prefix: str
        :param dataname: dataname
        :type dataname: str
        :param raw_packet: raw interest packet
        :type bytes: 
        :return: command, interest_param, app_param
        """
        # make a irreg command name with args
        command = prefix + "/" + PSKCmd.commands["CMD_MR"] + dataname
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_4
        # make app_param for Infomation Registry (raw interest packet)
        str_rawpacket = rawpacket.decode('utf-8')
        param = PSKParameters(rawpacket=str_rawpacket)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

    def make_irmod_cmd(self, prefix, dataname, rawpacket:BinaryStr=None) -> (str, Any):
        """
        make irmod command
        :param prefix: ir_prefix
        :type prefix: str
        :param dataname: dataname
        :type dataname: str
        :param rawpacket: raw interest packet
        :type bytes: 
        :return: command, interest_param, app_param
        """
        # make a irmod command name with args
        command = prefix + "/" + PSKCmd.commands["CMD_MM"] + dataname
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_4
        # make app_param for Infomation Registry (raw interest packet)
        str_rawpacket = rawpacket.decode('utf-8')
        param = PSKParameters(rawpacket=str_rawpacket)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

    def make_irdel_cmd(self, prefix, dataname, rawpacket:BinaryStr=None) -> (str, Any):
        """
        make irdel command
        :param prefix: ir_prefix
        :type prefix: str
        :param dataname: dataname
        :type dataname: str
        :param rawpacket: raw interest packet
        :type bytes: 
        :return: command, interest_param, app_param
        """
        # make a irmod command name with args
        command = prefix + "/" + PSKCmd.commands["CMD_MD"] + dataname
        # set interest parameter
        i_param = InterestParam()
        i_param.must_be_fresh = True
        i_param.nonce = gen_nonce()
        i_param.lifetime = INT_LT_4
        # make app_param for Infomation Registry (raw interest packet)
        str_rawpacket = rawpacket.decode('utf-8')
        param = PSKParameters(rawpacket=str_rawpacket)
        str_app_param = json.dumps(param, default=serialize);
        return command, i_param, bytes(str_app_param, 'utf-8')

# TODO:
    def make_bakdifs_cmd(self, prefix, dataname, raw_packet) -> (str, Any):
        pass
