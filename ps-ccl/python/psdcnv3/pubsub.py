"""
PS-CCL client API for Python
"""

from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
from ndn.encoding import Name, InterestParam
from ndn.encoding.ndn_format_0_3 import parse_data
import json
import time
import asyncio
import nest_asyncio

nest_asyncio.apply(asyncio.get_event_loop())

from .pskcmd import *
from .pskinfo import *

def normalize(name):
    return name if name.startswith("/") else ("/" + name)

def populate(option, params):
    if type(params) == str:
        params = json.loads(params)
    for key in params:
        option[key] = params[key]
    return option

def invoke_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

class Pubsub(object):
    """
    PSDCNv3 Pubsub client.
    Can be used for both publishers and subscribers.
    
    :ivar face: a face (a connection to a forwarder, known as `app` in python-ndn)
    :ivar pub_prefix (optional): prefix of the publisher for data exchange with the broker
    """

    def __init__(self, face, svc_name=None, pub_prefix="/pub1_prefix"):
        self.face = self.app = face
        self.keeper = PSKCmd(svc_name)
        self.pub_prefix = pub_prefix

    def pubadv(self, dataname, onSuccess, onFailure, params={}):
        """
        Pubsub function for issuing publish-advertise requests.

        :param dataname: data name which publications will be made to.
        :type dataname: str
        :param onSuccess:
            callback function of dataname which is called when the request was successful
        :type onSuccess: function of (str) -> None
        :param onFailure:
            callback function of dataname and a reason (message) of error
                which is called when the request was unsuccessful.
        :type onFailure: function of (str, str) -> None
        :param params: dict of keys from 'topicscope', 'storagetype', 'storageprefix' and 'redefine'
            where 'topicscope' is scope of the topic (TopicScope.GLOBAL/default, TopicScope.LOCAL)
                  'storeagetype' is the type of storage for the data name
                      (StorageType.BROKER/default, StorageType.PUBLISHER, StorageType.DIFS)
                  'storageprefix' is the prefix for the publisher storage or DIFS storage.
                      (Must be provided with `storagetype` being StorageType.PUBLISHER or
                       StorageType.DIFS.)
                  'redefine' is a flag to inform if redefinition is allowed.(False)
        :type params: dict or a JSON string
        :return: True(succes) or False(failure)
        :rtype: bool
        """
        # Preamble
        dataname = normalize(dataname)
        pubadvinfo = populate(PubAdvInfo(dataname), params)

        # Make pubadv command
        if pubadvinfo['storageprefix']:
            if pubadvinfo['storagetype'] == StorageType.BROKER:
                onFailure(dataname,
                    f"Storagetype not PUBLISHER or DIFS given {pubadvinfo['storageprefix']}")
                return False
        command, int_param, app_param = self.keeper.make_pubadv_cmd(
            self.keeper.svc_name, dataname, pubadvinfo=pubadvinfo)

        # Fire the command
        try:
            int_name, meta, content = invoke_async(
                self.face.express_interest(
                    Name.from_str(command), interest_param=int_param, app_param=app_param
                )
            )
            content = json.loads(bytes(content).decode())
            if content['status'] == 'OK':
                onSuccess(dataname)
                return True
            else:
                reason = content['reason'] if 'reason' in content else "Unknown pubadv error"
                onFailure(dataname, reason)
                return False
        except Exception as e:
            onFailure(dataname, f"{type(e).__name__}")
            return False

    def pubunadv(self, dataname, onSuccess, onFailure, params={}):
        """
        Pubsub function for issuing publish-unadvertise requests.

        :param dataname: data name which publications will be made to.
        :type dataname: str
        :param onSuccess:
            callback function of dataname which is called when the request was successful
        :type onSuccess: function of (str) -> None
        :param onFailure:
            callback function of dataname and a reason (message) of error
                which is called when the request was unsuccessful.
        :type onFailure: function of (str, str) -> None
        :param params: dict of keys from 'topicscope', and 'allow_undefined'
            where 'topicscope' is the scope of topic (TopicScope.GLOBAL/default, TopicScope.LOCAL)
                  'allow_undefined' is a flag to inform 
                      if unadvertising an undefined name is allowed. (True)
        :type params: dict or JSON string
        :return: True(succes) or False(failure)
        :rtype: bool
        """
        # Preamble
        dataname = normalize(dataname)
        pubadvinfo = populate(PubAdvInfo(dataname), params)

        # Make pubunadv command
        command, int_param, app_param = self.keeper.make_pubunadv_cmd(
            self.keeper.svc_name, dataname, pubadvinfo=pubadvinfo)

        # Fire the command
        try:
            int_name, meta, content = invoke_async(
                self.face.express_interest(
                    Name.from_str(command), interest_param=int_param, app_param=app_param
                )
            )
            content = json.loads(bytes(content).decode())
            if content['status'] == 'OK' or pubadvinfo['allow_undefined']:
                onSuccess(dataname)
                return True
            else:
                onFailure(dataname, content['reason'] if 'reason' in content else "Unknown error")
                return False
        except Exception as e:
            onFailure(dataname, f"{type(e).__name__}")
            return False

    def pubdata(self, dataname, seq, item, onSuccess, onFailure):
        """
        Pubsub function for issuing bulk data publication requests.

        :param dataname: data name which publications will be made to.
        :type dataname: str
        :param seq: sequence number
        :type seq: int
        :param item: data item to be published
        :type item: Any (that can be stringified)
        :param onSuccess:
            callback function of dataname and seq which is called when the request was successful
        :type onSuccess: function of (str, int) -> None
        :param onFailure:
            callback function of dataname, seq and a reason (message) of error
                which is called when the request was unsuccessful.
        :type onFailure: function of (str, int, str) -> None
        :return: True(succes) or False(failure)
        :rtype: bool
        """
        # Preamble
        dataname = normalize(dataname)
        seq = int(seq)
        data_pos = dataname + "/" + str(seq)

        # Handler for data item publication
        def send_data(int_name, int_param, app_parram):
            self.face.put_data(int_name, content=item.encode(), freshness_period=1)

        # Add a router for data transmission
        try:
            invoke_async(self.face.register(dataname, send_data))
        except:
            onFailure(dataname, seq, f"Couldn't register route {dataname}")
            return False

        # Do the publication allowing up to 3 times of retrial
        success = True
        trial_times = 1
        while True:
            try:
                # Make transmission request and wait for completion
                pubdatainfo = PubDataInfo(
                    data_prefix=dataname, data_sseq=seq, data_eseq=seq,
                    pub_prefix=self.pub_prefix)
                command, int_param, app_param = \
                    self.keeper.make_pubdata_cmd(self.keeper.svc_name, dataname,
                        seq, pubdatainfo)
                int_name, meta, content = invoke_async(
                    self.face.express_interest(
                        Name.from_str(command), interest_param=int_param, app_param=app_param
                    )
                )
                # Transmission completed
                content = json.loads(bytes(content).decode())
                if content['status'] != 'OK' or int(content['value']) != 1:
                    success = False
                    reason = content['reason'] if 'reason' in content \
                                               else 'Unknown pubdata error'
                if content['status'] != 'OK':   # Hopeless, return immediately
                    # onFailure(dataname, seq, reason)
                    break
            except (InterestNack, InterestTimeout):
                success = False
                reason = f"Broker unreachable or timeout"
            except Exception as e:
                success = False
                reason = f"{type(e).__name__} {str(e)}"
            if success:
                break
            trial_times += 1
            if trial_times > 3:
                break
        # Unregister route
        try:
            invoke_async(self.face.unregister(dataname))
        except:
            pass
        if success:
            onSuccess(dataname, seq)
            return True
        else:
            onFailure(dataname, seq, reason)
            return False

    def subtopic(self, topicname, onSuccess, onFailure, params={}):
        """
        Pubsub function for issuing topic-subscription requests.

        :param topicname: topic name which subscriptions is made against.
            May include MQTT-style wildcard characters such as + and #.
        :type topicname: str
        :param onSuccess:
            callback function of topicname and {dataname: [rn_name]} which is called when
                the request was successful
        :type onSuccess: function of (str, {str: [str]}) -> None
        :param onFailure:
            callback function of topicname and a reason (message) of error
                which is called when the request was unsuccessful.
        :type onFailure: function of (str, str) -> None
        :param params: dict of keys from 'servicetoken', and 'exclude'
            where 'servicetoken' is magic token for service validation, and
                  'exclude' is prefixes of data names to exclude from the result 
        :type params: dict or a JSON string
        :return: True(succes) or False(failure)
        :rtype: bool
        """
        # Preamble
        topicname = normalize(topicname)
        subinfo = populate(SubInfo(), params)

        # Make subtopic command
        command, int_param, app_param = \
            self.keeper.make_subtopic_cmd(self.keeper.svc_name, normalize(topicname),
                subinfo=subinfo)

        # Fire the command
        try:
            int_name, meta, content = invoke_async(
                self.face.express_interest(
                    Name.from_str(command), interest_param=int_param, app_param=app_param
                )
            )
            content = json.loads(bytes(content).decode())
        except Exception as e:
            onFailure(topicname, f"{type(e).__name__}")
            return False
        if content['status'] != 'OK':
            reason = content['reason'] if 'reason' in content else "Unknown subtopic error"
            onFailure(topicname, reason)
            return False
        values = content['value']

        # Process exclusion list
        exclude = subinfo['exclude']
        if not exclude:
            onSuccess(topicname, {v[0]: v[1] for v in values})
            return True
        if type(exclude) != list:
            exclude = [str(exclude)]
        onSuccess(topicname, {v[0]: v[1] for v in values 
                                         if not any(v[0].startswith(e) for e in exclude)})
        return True

    def submani(self, dataname, rn_name, onSuccess, onFailure):
        """
        Pubsub function for issuing data-manifest requests.

        :param dataname: data name where the data manifest will be found.
            Should be one of the valid data names of `rn_names` obtained by
            a recent `suptopic` request.
        :type dataname: str
        :param rn_name: rn name which the data will be fetched from.
            Should be a valid rn name obtained by a recent `subtopic` request.
        :type rn_name: str
        :param onSuccess:
            callback function of dataname and (rn_name, fst, lst)
                which is called when the request was successful
        :type onSuccess: function of (str, (str, int, int)) -> None
        :param onFailure:
            callback function of dataname and a reason (message) of error
                which is called when the request was unsuccessful.
        :type onFailure: function of (str, str) -> None
        :return: True(succes) or False(failure)
        :rtype: bool
        """
        # Preamble
        dataname = normalize(dataname)
        rn_name = normalize(rn_name)
        command, int_param, app_param = self.keeper.make_submani_cmd(dataname, rn_name)
        try:
            int_name, meta, content = invoke_async(
                self.face.express_interest(
                    Name.from_str(command), interest_param=int_param, app_param=app_param
                )
            )
            content = json.loads(bytes(content).decode())
            if content['status'] == 'OK':
                onSuccess(dataname, (rn_name, content['fst'], content['lst']))
                return True
            else:
                reason = content['reason'] if 'reason' in content \
                                           else f"Name {dataname} not found in store"
            return False
        except Exception as e:
            reason = f"{type(e).__name__} {str(e)}"
        onFailure(dataname, reason)
        return False
 
    def sublocal(self, topicname, onSuccess, onFailure, params={}):
        """
        Pubsub function for issuing topic-subscription to local broker requests.

        :param topicname: topic name which subscriptions is made to.
            Can also include MQTT-style wildcard characters such as + and #.
        :type topicname: str
        :param onSuccess:
            callback function of rn_name and [(dataname, fst, lst)] which is called when
                the request was successful
        :type onSuccess: function of (str, [(str, int, int)]) -> None
        :param onFailure:
            callback function of topicname and a reason (message) of error
                which is called when the request was unsuccessful.
        :type onFailure: function of (str, str) -> None
        :param params: dict of keys from 'servicetoken', and 'exclude'
            where 'servicetoken' is magic token for service validation, and
                  'exclude' is prefix(es) of data names to exclude from the result 
        :type params: dict or a JSON string
        :return: True(succes) or False(failure)
        :rtype: bool
        """
        # Preamble
        topicname = normalize(topicname)
        subinfo = populate(SubInfo(topicscope=TopicScope.LOCAL), params)

        # Make sublocal command
        command, interest_param, app_param = \
            self.keeper.make_subtopic_cmd(self.keeper.svc_name, normalize(topicname),
                local=True, subinfo=subinfo)

        # Fire the command
        try:
            int_name, meta, content = invoke_async(
                self.face.express_interest(
                    Name.from_str(command), interest_param=int_param, app_param=app_param
                )
            )
            content = json.loads(bytes(content).decode())
            if content['status'] != 'OK':
                reason = content['reason'] if 'reason' in content \
                                           else f"No matches for topic {topicname}"
                onFailure(topicName, reason)
                return False
        except Exception as e:
            onFailure(topicName, f"{type(e).__name__}")
            return False

        # Process exclusion list
        values = content['value']['manifests']
        if exclude:
            if type(exclude) != list:
                exclude = [str(exclude)]
            values = [v for v in values if not any(v[0].startswith(e) for e in exclude)]

        # All done
        onSuccess(content['value']['broker'], values)
        return True

    def subdata(self, dataname, seq, forward_to, lifetime=None):
        """
        Pubsub function for issuing data requests.

        :param dataname: data name where the data will be found.
            Should be one of the valid names obtained by a recent `subtopic` request.
        :type dataname: str
        :param seq: index of the data published under `dataname`.
        :type seq: int
        :param forward_to: forwarding hint information as the prefix of a broker.
        :type forward_to: str
        :param lifetime: time extent until which the interest should be kept alive.
        :type lifetime: int (in miliseconds)
        :return: Data found under the given data name and sequence number.
            None if no such data exists.
            (Can also occur InterestNack or InterestTimeout exceptions.)
        """
        command, int_param, app_param = \
            self.keeper.make_subdata_cmd(dataname, seq, forward_to, lifetime)
        int_name, meta, content = invoke_async(
            self.face.express_interest(Name.from_str(command), interest_param=int_param)
        )
        return bytes(content) if content else None

### Pubsub
