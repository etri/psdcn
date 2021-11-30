from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
from ndn.encoding import Name, InterestParam
from ndn.utils import gen_nonce
import asyncio
import json

from psdcnv3.psk import *
from psdcnv3.utils import *

def normalize(name):
    return name if name.startswith("/") else ("/" + name)

class Pubsub(object):
    """
    PSDCNv3 Pubsub client.
    Can be used for both publishers and subscribers.
    
    :ivar app: an ndn.app.NDNApp instance
    :ivar keeper: PS Keeper instance
    :ivar pub_prefix (optional): prefix of the publisher for data exchange with the broker
    """

    def __init__(self, app, pub_prefix=None):
        self.app = app
        self.keeper = PSKCmd(app)
        self.pub_prefix = pub_prefix

    async def pubadv(self, dataname,
            topicscope=TopicScope.GLOBAL,
            storagetype=StorageType.BROKER,
            storageprefix=None,
            redefine=False):
        """
        Coroutine function for issuing publish-advertise requests.

        :param dataname: data name which publications will be made to.
        :type dataname: str
        :param topicscope: scope of the topic (TopicScope.GLOBAL=0, TopicScope.LOCAL=1)
        :type topicscope: int
        :param storagetype: type of storage for the data name
            (StorageType.BROKER=0, StorageType.PUBLISHER=1, StorageType.DIFS=2)
        :type storagetype: int
        :param storageprefix: prefix for the publisher storage or DIFS storage.
            (Must be provided with `storagetype` being StorageType.PUBLISHER or StorageType.DIFS.)
        :type storageprefix: string
        :param redefine: flag to inform if redefinition is allowed. (False)
        :type redefine: bool
        :return: True if `dataname` successfully advertised. False otherwise.
            (If False, `self.reason` keeps a descriptive explanation of the error.)
        """
        dataname = normalize(dataname)
        pubadvinfo = PubAdvInfo(dataname, redefine=redefine)
        if storageprefix:
            if storagetype == StorageType.BROKER:
                self.reason = f"Storagetype not PUBLISHER or DIFS given {storageprefix}"
                return False
            pubadvinfo["storagetype"] = StorageType.PUBLISHER
            pubadvinfo["storageprefix"] = storageprefix
        pubadvinfo["topicscope"] = topicscope
        command, int_param, app_param = \
            self.keeper.make_pubadv_cmd(self.keeper.svc_name, dataname, pubadvinfo=pubadvinfo)
        try:
            _, _, content = await self.app.express_interest(
                Name.from_str(command), interest_param=int_param, app_param=app_param)
            content = json.loads(bytes(content).decode())
        except Exception as e:
            self.reason = f"{type(e).__name__} {str(e)}"
            return False
        if content['status'] == 'OK':
            return True
        self.reason = content['reason'] if 'reason' in content else "Unknown pubadv error"
        return False

    async def pubunadv(self, dataname,
            topicscope=TopicScope.GLOBAL,
            allow_undefined=True):
        """
        Coroutine function for issuing publish-unadvertise requests.

        :param dataname: data name which no more publications will be allowed to.
        :type dataname: str
        :param topicscope: scope of the topic (TopicScope.GLOBAL=0, TopicScope.LOCAL=1)
        :type topicscope: int
        :param allow_undefined: flag to inform if undefined name is allowed. (True)
        :type allow_undefined: bool
        :return: True if `dataname` successfully unadvertised. False otherwise.
            (If False, `self.reason` keeps a descriptive explanation of the error.)
        """
        dataname = normalize(dataname)
        pubadvinfo = PubAdvInfo(dataname)
        pubadvinfo["topicscope"] = topicscope
        command, int_param, app_param = \
            self.keeper.make_pubunadv_cmd(self.keeper.svc_name, dataname, pubadvinfo=pubadvinfo)
        try:
            _, _, content = await self.app.express_interest(
                Name.from_str(command), interest_param=int_param, app_param=app_param)
            content = json.loads(bytes(content).decode())
        except Exception as e:
            self.reason = f"{type(e).__name__} {str(e)}"
            return False
        if content['status'] == 'OK' or allow_undefined:
            return True
        self.reason = content['reason'] if 'reason' in content else "Unknown pubunadv error"
        return False

    async def pubdata(self, dataname, data, seq1, seq2=0):
        """
        Coroutine function for issuing bulk data publication requests.

        :param dataname: data name which publications will be made to.
        :type dataname: str
        :param data: data to be published
        :type data: [any] (listified automatically if not given a list)
        :param seq1: start (first) sequence number
        :type seq1: int
        :param seq2: end (last) sequence number. If not given, it is set as `seq1`.
        :type seq2: int
        :return: True if the publication was successful. False otherwise.
            (If False, `self.reason` keeps a descriptive explanation of the error.)
        """
        dataname = normalize(dataname)
        seq1, seq2 = int(seq1), int(seq2)
        if seq2 == 0:
            seq2 = seq1
        n_items = seq2 - seq1 + 1
        if type(data) is not list:
            data = [data]
        if len(data) != n_items:
            self.reason = "Data number mismatch"
            return False

        # Handler for data item publication which will be called n_items times
        def send_data(int_name, int_param, app_parram):
            # Simple command parser
            name = Name.to_str(int_name).split("/params-sha256")[0].split("/")[1:]
            seqn = int(name[-1])
            # Send one data item to the broker
            self.app.put_data(int_name, content=data[seqn-seq1].encode(), freshness_period=1)

        # Add a router for data transmission
        try:
            await self.app.register(dataname, send_data)
        except:
            self.reason = f"Couldn't register route {dataname}"
            return False

        # Do the publication allowing up to 3 times of retrial
        success = True
        trial_times = 1
        while True:
            try:
                # Make transmission request and wait for completion
                pubdatainfo = PubDataInfo(
                    data_prefix=dataname, data_sseq=seq1, data_eseq=seq2,
                    pub_prefix=self.pub_prefix)
                command, int_param, app_param = \
                    self.keeper.make_pubdata_cmd(self.keeper.svc_name, dataname,
                        seq1, pubdatainfo)
                _, _, content = await self.app.express_interest(Name.from_str(command),
                    interest_param=int_param, app_param=app_param)
                # Transmission completed or error occurred
                content = json.loads(bytes(content).decode())
                if content['status'] != 'OK' or int(content['value']) != n_items:
                    success = False
                    self.reason = \
                        content['reason'] if 'reason' in content else 'Unknown pubdata error'
                    if content['status'] != 'OK':   # Hopeless, return immediately
                        break
            except (InterestNack, InterestTimeout):
                success = False
                self.reason = f"Broker unreachable or timeout"
                await asyncio.sleep(1.0)
            except Exception as e:
                success = False
                self.reason = f"{type(e).__name__} {str(e)}"
            if success:
                break
            trial_times += 1
            if trial_times > 3:
                break
        # Unregister route
        try:
            await self.app.unregister(dataname)
        except:
            pass
        return success

    async def subtopic(self, topicname, servicetoken=None, exclude=None):
        """
        Coroutine function for issuing topic-subscription requests.

        :param topicname: topic name which subscriptions is made to.
            Can also include MQTT-style wildcard characters such as + and #.
        :type topicname: str
        :param servicetoken: magic token for service validation
        :type servicetoken: str
        :param exclude: prefixes of data names to exclude from the result
        :type exclude: str or [str] (defaults to None)
        :return: dict of {dataname: [rn_name]} that matches the given topic name.
            (If error occurs, returns {} and `self.reason` keeps a descriptive explanation
             of the error.)
        :rtype: dict of {str: [str]}
        """
        topicname = normalize(topicname)
        subinfo = SubInfo(topicscope=TopicScope.GLOBAL)
        if servicetoken is not None:
            subinfo["servicetoken"] = str(servicetoken)
        command, int_param, app_param = \
            self.keeper.make_subtopic_cmd(self.keeper.svc_name, topicname,
                subinfo=subinfo)
        try:
            _, _, content = await self.app.express_interest(
                Name.from_str(command), interest_param=int_param, app_param=app_param)
            content = json.loads(bytes(content).decode())
        except Exception as e:
            self.reason = f"{type(e).__name__} {str(e)}"
            return {}
        if content['status'] != 'OK':
            self.reason = content['reason'] if 'reason' in content else "Unknown subtopic error"
            return {}
        values = content['value']
        # Process exclusion list
        if not exclude:
            return {v[0]: v[1] for v in values}
        if type(exclude) != list:
            exclude = [str(exclude)]
        return {v[0]: v[1] for v in values if not any(v[0].startswith(e) for e in exclude)}

    async def submani(self, dataname, rn_name):
        """
        Coroutine function for issuing data-manifest requests.

        :param dataname: data name where the data manifest will be found.
            Should be one of the valid data names of `rn_names` obtained by
            a recent `subtopic` request.
        :type dataname: str
        :param rn_name: rn name which the data will be fetched from.
            Should be valid a rn name obtained by a recent `subtopic` request.
        :type rn_names: str
        :return: (rn_name, fst, lst)
            `fst` is the starting index of current batch,
            and `lst` is the last index of current batch under the given data name.
            (If error occurs, returns None and
             `self.reason` keeps a descriptive explanation of the error.)
        :rtype: (str, int, int)
        """
        dataname = normalize(dataname)
        rn_name = normalize(rn_name)
        command, int_param, app_param = self.keeper.make_submani_cmd(dataname, rn_name)
        try:
            _, _, content = await self.app.express_interest(
                Name.from_str(command), interest_param=int_param, app_param=app_param)
            content = json.loads(bytes(content).decode())
            if content['status'] == 'OK':
                return (rn_name, content['fst'], content['lst'])
            self.reason = content['reason'] \
                if 'reason' in content else "Unknown submani error"
        except Exception as e:
            self.reason = f"{type(e).__name__} {str(e)}"
        return None

    async def sublocal(self, topicname, servicetoken=None, exclude=None):
        """
        Coroutine function for issuing topic-subscription to local broker requests.

        :param topicname: topic name which subscriptions is made to.
            Can also include MQTT-style wildcard characters such as + and #.
        :type topicname: str
        :param servicetoken: magic token for service validation.
        :type servicetoken: str
        :param exclude: prefixes of data names to exclude from the result
        :type exclude: str or [str] (defaults to None)
        :return: node_name, [(dataname, fst, lst)]
            (If error occurs, returns None, [] and
             `self.reason` keeps a descriptive explanation of the error.)
        :rtype: str, [(str, int, int)]
        """
        topicname = normalize(topicname)
        subinfo = SubInfo(topicscope=TopicScope.LOCAL)
        if servicetoken is not None:
            subinfo["servicetoken"] = str(servicetoken)
        command, interest_param, app_param = \
            self.keeper.make_subtopic_cmd(self.keeper.svc_name, topicname,
                local=True, subinfo=subinfo)
        try:
            _, _, content = await self.app.express_interest(
                Name.from_str(command), interest_param=interest_param, app_param=app_param)
            content = json.loads(bytes(content).decode())
            if content['status'] != 'OK':
                self.reason = content['reason'] \
                    if 'reason' in content else "Unknown sublocal error"
                return None, []
        except Exception as e:
            self.reason = f"{type(e).__name__} {str(e)}"
            return None, []
        # Process exclusion list
        values = content['value']['manifests']
        if exclude:
            if type(exclude) != list:
                exclude = [str(exclude)]
            values = [v for v in values if not any(v[0].startswith(e) for e in exclude)]
        # All done
        return content['value']['broker'], values

    async def subdata(self, dataname, seq, forward_to, lifetime=None):
        """
        Coroutine function for issuing data requests.

        :param dataname: data name where the data will be found.
            Should be one of the valid names obtained by a recent `suptopic` request.
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
                self.keeper.make_subdata_cmd(normalize(dataname), seq, forward_to, lifetime)
        _, _, fetched = await self.app.express_interest(
            Name.from_str(command), interest_param=int_param)
        return bytes(fetched) if fetched else None

