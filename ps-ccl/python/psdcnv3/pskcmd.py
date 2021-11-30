"""
PSK interface for PSDCNv3.
These interfaces are to make commands for publisher, subscriber, and broker.
"""

from ndn.encoding import Name, InterestParam
from ndn.utils import gen_nonce
from .pskinfo import *

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
    """
    Keeper object provides interface for making PSDCNv3 command names.
    """
    def __init__(self, svc_name=None):
        self.svc_name = svc_name if svc_name else "/etri/rn"

    def make_generic_cmd(self, command:str, prefix:str, dataname:str="/_", seq:int=None,
            **kwargs):
        """
        make generic command
        :param prefix: network_prefix or broker_prefix
        :type prefix: str
        :param dataname: dataname for publishing data
        :type dataname: str
        :return: Interest of (command, interest_param, app_param)
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
                        irinfo:IRInfo=None, rninfo:RNInfo=None):
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
        :return: Interest of (command, interest_param, app_param)
        """
        # make a pubadv command name with args
        command = prefix + "/PA" + dataname
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(
                    pubadvinfo=pubadvinfo, irinfo=irinfo, rninfo=rninfo))
        return command, int_param, app_param

    def make_pubunadv_cmd(self, prefix, dataname, pubadvinfo:PubAdvInfo=None):
        """
        make pubunadv command
        :param prefix: network_prefix or broker_prefix
        :type prefix: str
        :param dataname: dataname for unpublishing data
        :type dataname: str
        :param pubadvinfo: pub information
        :type pubadvinfo: 
        :return: Interest of (command, interest_param, app_param)
        """
        # make a pubunadv command name with args
        command = prefix + "/PU" + dataname
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(pubadvinfo=pubadvinfo))
        return command, int_param, app_param

    def make_pubdata_cmd(self, prefix, dataname, seq, pubdatainfo:PubDataInfo=None):
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
        :return: Interest of (command, interest_param, app_param)
        """
        # make a pubdata command name with args
        command = prefix + "/PD" + dataname + '/' + str(seq)
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(pubdatainfo=pubdatainfo))
        return command, int_param, app_param

    def make_subtopic_cmd(self, prefix, dataname, local=False, subinfo:SubInfo=None):
        """
        make subtopic command
        :param prefix: network_prefix or topicrn_prefix
        :type prefix: str
        :param dataname: topic name
        :type dataname: str
        :param subinfo: subscription information
        :type subinfo: SubInfo
        :return: Interest of (command, interest_param, app_param)
        """
        # make a subtopic command name with args
        command = prefix + ("/SL" if local else "/ST") + dataname
        int_param = make_int_param()
        app_param = make_app_param(PSKParameters(subinfo=subinfo))
        return command, int_param, app_param

    def make_submani_cmd(self, dataname, forward_to):
        """
        make submani command
        :param dataname: topic name
        :type dataname: str
        :param forward_to: network_prefix or topicrn_prefix
        :type forward_to: str
        :return: Interest of (command, interest_param, app_param)
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
        :param forward_to: network_prefix or topicrn_prefix
        :type forward_to: str
        :param lifetime: interest lifetime in miliseconds
        :type seq: int
        :return: Interest of (command, interest_param, None)
        """
        # make a data request
        command = dataname + "/" + str(seq)
        int_param = make_int_param()
        int_param.must_be_fresh = False
        int_param.can_be_prefix = True  # Caching for dual CS enablement
        int_param.forwarding_hint = [(0, forward_to)]
        if lifetime:
            int_param.lifetime = lifetime
        return command, int_param, None

