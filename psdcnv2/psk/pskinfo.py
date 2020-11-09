"""
PSK Information data for PSDCNv2.
These classes provide informaitn for publisher, subscriber, broker and IR.
"""

from datetime import datetime, date, time
import json


def serialize(obj):
    """
    JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, date):
        serial = obj.isoformat()
        return serial
    if isinstance(obj, time):
        serial = obj.isoformat()
        return serial
    # return obj.__dict__
    return str(obj)


class ObjectDeserialize(dict):
    def __init__(self):
        pass
     
    def decode(self, s):
        d = json.loads(s);
        if d is not None:
            self.update(d)
        return self


class StorageType(object):
    BROKER = 0
    PUBLISHER = 1
    DIFS = 2


class TopicScope(object):
    GLOBAL = 0
    LOCAL = 1


class PubAdvInfo(ObjectDeserialize):
    """
    Publish Information for PSDCNv2.
    This is required by publisher to publish the data to RN.
    variables
    storagetype: publisher/broker/difs
    dataname: /etri/bld7/room385/temp
    topicscope: local/global/dual
    bundle: on/off
    startseq: 1
    actionexceeddatapktcnt: difs/del
    maxdatapktcnt: 100
    """
    def __init__(self, storagetype:str=None, pubprefix:str=None, dataname:str=None,
                 topicscope:TopicScope=TopicScope.GLOBAL, bundle:bool=False, bundlesize:int=0,
                 startseq:int=None, actionexceeddatapktcnt:str=None, maxdatapktcnt:int=None,
                 redefine:bool=False, **kwargs):
        super(ObjectDeserialize).__init__()
        
        self['storagetype'] = storagetype
        self['pubprefix'] = pubprefix
        self['dataname'] = dataname
        self['topicscope'] = topicscope
        self['bundle'] = bundle
        self['bundlesize'] = bundlesize
        self['startseq'] = startseq
        self['redefine'] = redefine
        self['actionexceeddatapktcnt'] = actionexceeddatapktcnt
        self['maxdatapktcnt'] = maxdatapktcnt
        self.update(kwargs)


class PubDataInfo(ObjectDeserialize):
    """
    Publish data for PSDCNv2.
    This is required by publisher to publish the data to RN.
    variables
    data: published data for small data
    data_prefix: /etri/bld7/room385/temp for large data
    data_sseq: 10 for large data
    data_eseq: 20 for large data
    """
    def __init__(self, data:bytes=None, data_prefix:str=None,
                 data_sseq:int=None, data_eseq:int=None,
                 **kwargs):
        super(ObjectDeserialize).__init__()
        
        self['data'] = data
        # self['data_prefix'] = data_prefix
        self['data_sseq'] = data_sseq
        self['data_eseq'] = data_eseq
        self.update(kwargs)


class SubInfo(ObjectDeserialize):
    """
    Subscribe data for PSDCNv2.
    This data is required by subscriber to register to broker.
    variables
    topicscope: local/global/dual
    servicetoken: 1234DFAENDNDJEDMM343DD
    is_bundled: bool
    """
    def __init__(self, topicscope:str=TopicScope.GLOBAL, servicetoken:str=None,
                 is_bundled:bool=False, **kwargs):
        super(ObjectDeserialize).__init__()
        self['topicscope'] = topicscope
        self['servicetoken'] = servicetoken
        self['is_bundled'] = is_bundled
        self.update(kwargs)


class RNInfo(ObjectDeserialize):
    """
    Rendezvous node data for PSDCNv2.
    This data is required by data-rn to send brokername to topic-rn.
    variables
    brokername: broker-2
    """
    def __init__(self, brokername:str=None, **kwargs):
        super(ObjectDeserialize).__init__()
        self['brokername'] = brokername
        self.update(kwargs)


class IRInfo(ObjectDeserialize):
    """
    Information Registry data for PSDCNv2.
    This data is required by broker to register with IR.
    variables
    id
    name: 
    providerid:
    price: 
    issue_date:
    expire_date:
    ketwards:
    origin
    region:
    description: 
    """
    def __init__(self, id:str=None, name:str=None, providerid:str=None,
                 price:float=None, issue_date:datetime=None, expire_date:datetime=None,
                 keywords:str=None, origin:str=None,
                 region:str=None, description:str=None,
                 **kwargs):
        super(ObjectDeserialize).__init__()
        self['id'] = id
        self['name'] = name
        self['providerid'] = providerid
        self['price'] = price
        self['issue_date'] = issue_date
        self['expire_date'] = expire_date
        self['keywords'] = keywords
        self['origin'] = origin
        self['region'] = region
        self['description'] = description
        self.update(kwargs)


class PSKParameters(ObjectDeserialize):
    """
    Making Application Parameter for PSDCNv2.
    This object is to make application parameter for Interest Packet.
    """
    def __init__(self, pubadvinfo:PubAdvInfo=None, pubdatainfo:PubDataInfo=None,
                 subinfo:SubInfo=None, rninfo:RNInfo=None, irinfo:IRInfo=None,
                 rawpacket:str=None, 
                 **kwargs):
        super(ObjectDeserialize).__init__()
        self['pubadvinfo'] = pubadvinfo
        self['pubdatainfo'] = pubdatainfo
        self['subinfo'] = subinfo
        self['rninfo'] = rninfo
        self['irinfo'] = irinfo
        self['rawpacket'] = rawpacket
        self.update(kwargs)

