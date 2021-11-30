"""
PSK Information data for PSDCNv3.
These classes provide informaitn for publisher, subscriber, broker and IR.
"""

from datetime import datetime, date, time
import json

NULL_STR = ''   # or None

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
    Publish Information for PSDCNv3.
    This is required by publisher to publish the data to RN.
    variables
    dataname: /etri/bld7/room385/temp
    storagetype: publisher/broker/difs
    topicscope: local/global/dual
    startseq: 1
    actionexceeddatapktcnt: difs/del
    maxdatapktcnt: 100
    """
    def __init__(self,
                 dataname:str=NULL_STR,
                 storagetype:StorageType=StorageType.BROKER,
                 topicscope:TopicScope=TopicScope.GLOBAL,
                 startseq:int=1,
                 # actionexceeddatapktcnt:str=NULL_STR,
                 maxdatapktcnt:int=100,
                 redefine:bool=False, **kwargs):
        super(ObjectDeserialize).__init__()
        
        self['dataname'] = dataname
        self['storagetype'] = storagetype
        self['topicscope'] = topicscope
        self['startseq'] = startseq
        self['redefine'] = redefine
        self['maxdatapktcnt'] = maxdatapktcnt
        # self['actionexceeddatapktcnt'] = actionexceeddatapktcnt
        self.update(kwargs)


class PubDataInfo(ObjectDeserialize):
    """
    Publish data for PSDCNv3.
    This is required by publisher to publish the data to RN.
    variables
    data_prefix: /etri/bld7/room385/temp
    data_sseq: 10
    data_eseq: 20
    pub_prefix: prefix of the publisher. /pub1_prefix
    """
    def __init__(self, data_prefix:str=NULL_STR,
                 data_sseq:int=None, data_eseq:int=None,
                 pub_prefix:str=NULL_STR,
                 **kwargs):
        super(ObjectDeserialize).__init__()
        
        # self['data'] = data
        self['data_prefix'] = data_prefix
        self['data_sseq'] = data_sseq
        self['data_eseq'] = data_eseq
        if pub_prefix:
            self['pub_prefix'] = pub_prefix
        self.update(kwargs)


class SubInfo(ObjectDeserialize):
    """
    Subscribe data for PSDCNv3.
    This data is required by subscriber to register to broker.
    variables
    topicscope: local/global/dual
    servicetoken: 1234DFAENDNDJEDMM343DD
    """
    def __init__(self, topicscope:str=TopicScope.GLOBAL, servicetoken:str=NULL_STR, **kwargs):
        super(ObjectDeserialize).__init__()
        self['topicscope'] = topicscope
        self['servicetoken'] = servicetoken
        self.update(kwargs)


class RNInfo(ObjectDeserialize):
    """
    Rendezvous node data for PSDCNv3.
    This data is required by data-rn to send brokername to topic-rn.
    variables
    brokername: broker-2
    """
    def __init__(self, brokername:str=NULL_STR, **kwargs):
        super(ObjectDeserialize).__init__()
        self['brokername'] = brokername
        self.update(kwargs)


class IRInfo(ObjectDeserialize):
    """
    Information Registry data for PSDCNv3.
    This data is required by broker to register with IR.
    variables
    id
    name: 
    providerid:
    price: 
    issue_date:
    expire_date:
    keywords:
    origin
    region:
    description: 
    """
    def __init__(self, id:str=NULL_STR, name:str=NULL_STR, providerid:str=NULL_STR,
                 price:float=None, issue_date:datetime=None, expire_date:datetime=None,
                 keywords:str=NULL_STR, origin:str=NULL_STR,
                 region:str=NULL_STR, description:str=NULL_STR,
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
    Making Application Parameter for PSDCNv3.
    This object is to make application parameter for Interest Packet.
    """
    def __init__(self, pubadvinfo:PubAdvInfo=None, pubdatainfo:PubDataInfo=None,
                 subinfo:SubInfo=None, rninfo:RNInfo=None, irinfo:IRInfo=None,
                 rawpacket:str=NULL_STR, 
                 **kwargs):
        super(ObjectDeserialize).__init__()
        self['pubadvinfo'] = pubadvinfo
        self['pubdatainfo'] = pubdatainfo
        self['subinfo'] = subinfo
        self['rninfo'] = rninfo
        self['irinfo'] = irinfo
        self['rawpacket'] = rawpacket
        self.update(kwargs)

