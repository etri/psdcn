/*
 * subinfo.hpp
 *
 * SubInfo class for SubTopic and SubData command
 */

#ifndef __SUBINFO_HPP__
#define __SUBINFO_HPP__

#include <string>
#include <memory>
#include "psdcn.hpp"

class SubInfo;
using SubInfoPtr = std::shared_ptr<SubInfo>;

class SubInfo {
public:
    uint32_t m_topicscope;// = 0 # global
    std::string m_servicetoken;

public:
    SubInfo();
    ~SubInfo();

    friend DocumentPtr toJson(SubInfoPtr &info);
    friend bool fromJson(DocumentPtr &ptree, SubInfoPtr &info);
    friend std::string toJsonString(SubInfoPtr &info);
    friend bool fromJsonString(std::string json, SubInfoPtr &info);
};

#endif /* __SUBINFO_HPP__ */
