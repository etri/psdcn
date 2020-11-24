from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout
from ndn.encoding import Name
import asyncio
import json, logging, uuid

from psdcnv2.psk import *
from psdcnv2.utils import *

def patch_dataname(dataname):
    return dataname if dataname.startswith("/") else ("/" + dataname)

class Pubsub(object):
    """
    PSDCNv2 Pubsub client.
    Can be used for both publishers and subscribers.
    
    :ivar app: an ndn.app.NDNApp instance
    """

    def __init__(self, app: NDNApp, id=None, scope=None, bundle=False):
        self.app = app
        self.id = id if id is not None else ("/" + str(uuid.uuid1()))
        self.scope = scope      # Defaults to TopicScope.GLOBAL
        self.bundle = bundle    # Can be overridden by individual pubadv request
        self.keeper = PSKCmd(app)
        self.logger = init_logger()

    def set_debug_mode(self, debug):
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        on_off = "on" if debug else "off"
        self.logger.info(f"Client {self.id}'s debugging turned {on_off}")

    async def pubadv(self, dataname,
            storagetype=None, bundle=None, bundlesize=None, pubprefix=None, redefine=False):
        """
        Coroutine function for issuing publish-advertise requests.

        :param dataname: data name which publications will be made to.
        :type dataname: str
        :param redefine: flag to inform if redefinition is allowed. (False)
        :type redefine: bool
        :return: True if `dataname` successfully advertised. False otherwise.
        """
        pubadvinfo = PubAdvInfo(storagetype=storagetype, redefine=redefine)
        if storagetype is not None and storagetype == StorageType.PUBLISHER:
            pubadvinfo["pubprefix"] = pubprefix
        if storagetype is None or storagetype == StorageType.BROKER:
            if bundle is None:
                bundle = self.bundle or bundlesize is not None
        if bundle:
            if bundlesize is not None and int(bundlesize) > 1:
                pubadvinfo["bundle"] = True
                pubadvinfo["bundlesize"] = int(bundlesize)
            else:
                self.logger.debug(f"** {dataname} won't be bundled due to bizarre bundle size")
                pass
        if self.scope is not None:  # Defaults to TopicScope.GLOBAL
            pubadvinfo["topicscope"] = self.scope
        command, interest_param, app_param = \
            self.keeper.make_pubadv_cmd(self.keeper.net_name, patch_dataname(dataname),
                pubadvinfo=pubadvinfo)
        data_name, meta_info, content = await self.app.express_interest(
            Name.from_str(command), interest_param=interest_param, app_param=app_param)
        content = json.loads(bytes(content).decode())
        status = content['status']
        if 'reason' in content:
            #self.logger.debug(f"** PA {dataname} failed. {content['reason']}")
            pass
        return content['status'] == 'OK'

    async def pubunadv(self, dataname, allow_undefined=True):
        """
        Coroutine function for issuing publish-unadvertise requests.

        :param dataname: data name which no more publications will be allowed to.
        :type dataname: str
        :param allow_undefined: flag to inform if undefined name is allowed. (True)
        :type allow_undefined: bool
        :return: True if `dataname` successfully unadvertised. False otherwise.
        """
        pubadvinfo = PubAdvInfo(topicscope=self.scope)
        command, interest_param, app_param = \
            self.keeper.make_pubunadv_cmd(self.keeper.net_name, patch_dataname(dataname),
                pubadvinfo=pubadvinfo)
        data_name, meta_info, content = await self.app.express_interest(
            Name.from_str(command), interest_param=interest_param, app_param=app_param)
        status = json.loads(bytes(content).decode())['status']
        return status == 'OK' or (allow_undefined and status == 'ERR')

    async def pubdata(self, dataname, data, seq=0):
        """
        Coroutine function for issuing data publication requests.

        :param dataname: data name which publications will be made to.
        :type dataname: str
        :param data: data to be published
        :type data: :any:
        :param seq: sequence position at which the data will be published.
            0 means append to the last position.
        :type seq: int
        :return: True if the publication was successful. False otherwise.
        """
        pubdatainfo = PubDataInfo(data=data)
        command, interest_param, app_param = \
            self.keeper.make_pubdata_cmd(self.keeper.net_name, patch_dataname(dataname), seq,
                pubdatainfo=pubdatainfo)
        data_name, meta_info, content = await self.app.express_interest(
            Name.from_str(command), interest_param=interest_param, app_param=app_param)
        content = json.loads(bytes(content).decode())
        if 'reason' in content:
            self.logger.debug(f"** PD to {dataname} failed. {content['reason']}")
        return content['status'] == 'OK' and int(content['value']) > 0

    async def pubdata2(self, dataname, data, seq1, seq2):
        """
        Coroutine function for issuing bulk data publication requests.

        :param dataname: data name which publications will be made to.
        :type dataname: str
        :param data: data to be published
        :type data: [any]
        :param seq1: start (first) sequence number
        :param seq2: end (last) sequence number
        :type seq1: int
        :type seq2: int
        :return: True if the publication was successful. False otherwise.
        """
        count = seq2 - seq1 + 1
        if len(data) != count:
            self.debug.warning(f"Large data number mismatch.")
            return False
        else:
            # Backup count count is to be decreased on each item publication
            n_items = count

        # Callback for data item publication which will be called n_items times
        def on_interest(interest_name, interest_param, app_parram):
            nonlocal count, seq1, seq2  # !!!
            # Simple command parser
            int_parse = Name.to_str(interest_name).split("/params-sha256")[0].split("/")[2:]
            dataname = "/" + "/".join(int_parse[:-1])
            seq = int(int_parse[-1])
            value = data[seq - seq1].encode()
            # Transmit a data item to the broker
            self.app.put_data(interest_name, content=value, freshness_period=1)
            count -= 1
            self.logger.debug(f"Data {dataname}[{seq}] published.")
            if count == 0:
                # Mission complete. Unregister route.
                asyncio.get_event_loop().create_task(self.app.unregister(self.id))

        # Add a router for bulk data transmission
        try:
            await self.app.register(self.id, on_interest)
        except:
            return False
        success = False
        try:
            pubdatainfo = PubDataInfo(prefix=self.id, data_sseq=seq1, data_eseq=seq2)
            command, interest_param, app_param = \
                self.keeper.make_pubdata_cmd(self.keeper.net_name, patch_dataname(dataname),
                    seq1, pubdatainfo)
            # Make transmission request and wait for completion
            data_name, meta_info, content = await self.app.express_interest(
                Name.from_str(command), interest_param=interest_param, app_param=app_param)
            # Transmission completed
            content = json.loads(bytes(content).decode())
            if 'reason' in content:
                self.logger.debug(f"** PD to {dataname} failed. {content['reason']}")
            success = content['status'] == 'OK'
            return success and int(content['value']) == n_items
        except InterestNack as e:
            self.logger.error(f"** InterestNack {e.reason} for pubdata2 {dataname}")
        except InterestTimeout as e:
            self.logger.error(f"** InterestTimeout for pubdata2 {dataname}")
        except Exception as e:
            self.logger.error(f"** {type(e).__name__} {str(e)}")
        return success

    async def subtopic(self, topicname, servicetoken=None, exclude=None):
        """
        Coroutine function for issuing topic-subscription requests.

        :param topicname: topic name which subscriptions is made to.
            Can include MQTT-style wild characters such as + and #.
        :type topicname: str
        :param exclude: prefixes of data names to exclude from the result
        :type exclude: str or [str] (defaults to None)
        :return: [(dataname, rn_name)] that match the given topic.
        :rtype: [(str, str)]
        """
        subinfo = SubInfo(topicscope=self.scope)
        if servicetoken is not None:
            subinfo["servicetoken"] = str(servicetoken)
        command, interest_param, app_param = \
            self.keeper.make_subtopic_cmd(self.keeper.net_name, patch_dataname(topicname),
                subinfo=subinfo)
        data_name, meta_info, content = await self.app.express_interest(
            Name.from_str(command), interest_param=interest_param, app_param=app_param)
        content = json.loads(bytes(content).decode())
        if content['status'] != 'OK':
            return []
        values = content['value']
        if exclude:
            if type(exclude) != list:
                exclude = [str(exclude)]
            values = [(k,v) for (k,v) in values
                if not any(k.startswith(e) for e in exclude)]
        return values

    async def submani(self, prefix, dataname):
        """
        Coroutine function for issuing data-manifest requests.

        :param prefix: rn-name from which the data will be fetched.
            Should be one of the valid rn-names obtained by recent `subtopic` request.
        :type prefix: str
        :param dataname: data name at which the data will be found.
            Should be one of the valid datanames from `prefix` obtained by
            recent `suptopic` request.
        :type dataname: str
        :return: (fst, lst, bundle_count, bundle_size)
            fst is the starting index of current batch (not bundled yet),
            and lst is the last index of current batch under the given data name.
            bundle_count and bundle_size are for number of bundles and
            size of each bundle.
            If no such data is found, (0, 0, 0, 0) is returned instead.
        :rtype: (int, int, int, int)
        """
        command, interest_param, app_param = \
            self.keeper.make_submani_cmd(prefix, patch_dataname(dataname))
        data_name, meta_info, content = await self.app.express_interest(
            Name.from_str(command), interest_param=interest_param, app_param=app_param)
        content = json.loads(bytes(content).decode())
        if content['status'] == 'OK':
            b_count = content['bundle_count'] if 'bundle_count' in content else 0
            b_size = content['bundle_size'] if 'bundle_size' in content else 0
            return content['fst'], content['lst'], b_count, b_size
        return 0, 0, 0, 0

    async def subdata(self, prefix, dataname, seq, is_bundled=False, lifetime=None):
        """
        Coroutine function for issuing data requests.

        :param prefix: rn-name from which the data will be fetched.
            Should be one of the valid rn-names obtained by recent `subtopic` request.
        :type prefix: str
        :param dataname: data name at which the data will be found.
            Should be one of the valid datanames from `prefix` obtained by
            recent `suptopic` request.
        :type dataname: str
        :param seq: index of the data published under `dataname`.
        :type seq: int
        :param lifetime: time extent until which the interest should be kept alive
        :type lifetime: int (in miliseconds)
        :return: Data found under the given data name and sequence number at `prefix`.
            None if no such data exists.
        """
        subinfo = SubInfo(is_bundled=is_bundled)
        command, interest_param, app_param = \
            self.keeper.make_subdata_cmd(prefix, patch_dataname(dataname), seq,
                subinfo=subinfo, lifetime=lifetime)
        data_name, meta_info, content = await self.app.express_interest(
            Name.from_str(command), interest_param=interest_param, app_param=app_param)
        content = json.loads(bytes(content).decode())
        if 'reason' in content:
            part = "bundle " if is_bundled else ""
            self.logger.debug(f"** SD {part}{dataname}[{seq}] failed. {content['reason']}")
        return content['value'] if 'value' in content else None
