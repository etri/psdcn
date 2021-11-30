/*
 * pubadvinfo.hpp
 *
 * PubAdvInfo class for PubAdv command
 */

#ifndef __PUBADVINFO_HPP__
#define __PUBADVINFO_HPP__

#include <string>
#include <memory>
#include "psdcn.hpp"

enum TopicScope {
    GLOBAL = 0,
    LOCAL = 1
};

enum StorageType {
    BROKER = 0,
    PUBLISHER = 1,
    DIFS = 2
};

class PubAdvInfo;
using PubAdvInfoPtr = std::shared_ptr<PubAdvInfo>;

class PubAdvInfo {
public:
    uint32_t m_storagetype;// = 0;    // broker
    std::string m_storageprefix;// = None
    std::string m_dataname;// = None
    uint32_t m_topicscope;// = 0 # global
    uint64_t m_startseq;// = 1
    bool m_redefine;// = false
    std::string m_actionexceeddatapktcnt;// = difs/del
    uint64_t m_maxdatapktcnt;// = 0

public:
    PubAdvInfo();
    ~PubAdvInfo();

    friend DocumentPtr toJson(PubAdvInfoPtr &info);
    friend bool fromJson(DocumentPtr &ptree, PubAdvInfoPtr &info);
    friend std::string toJsonString(PubAdvInfoPtr &info);
    friend bool fromJsonString(std::string json, PubAdvInfoPtr &info);
};

#endif /* __PUBADVINFO_HPP__ */
