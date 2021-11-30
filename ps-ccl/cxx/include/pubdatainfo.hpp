/*
 * pubdatainfo.hpp
 *
 * PubDataInfo class for PubData command
 */

#ifndef __PUBDATAINFO_HPP__
#define __PUBDATAINFO_HPP__

#include <string>
#include <memory>
#include "psdcn.hpp"

class PubDataInfo;
using PubDataInfoPtr = std::shared_ptr<PubDataInfo>;

class PubDataInfo {
public:
    std::string m_data_prefix;
    uint64_t m_data_sseq;
    uint64_t m_data_eseq;
    std::string m_pub_prefix;

public:
    PubDataInfo();
    ~PubDataInfo();

    friend DocumentPtr toJson(PubDataInfoPtr &info);
    friend bool fromJson(DocumentPtr &ptree, PubDataInfoPtr &info);
    friend std::string toJsonString(PubDataInfoPtr &info);
    friend bool fromJsonString(std::string json, PubDataInfoPtr &info);
};

#endif /* __PUBDATAINFO_HPP__ */
