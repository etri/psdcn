/*
 * irinfo.hpp
 *
 * IRInfo class for Marketplace
 */

#ifndef __IRINFO_HPP__
#define __IRINFO_HPP__

#include <string>
#include <memory>
#include "psdcn.hpp"

class IRInfo;
using IRInfoPtr = std::shared_ptr<IRInfo>;

class IRInfo {
public:
    std::string m_id;
    std::string m_name;
    std::string m_providerid;
    float m_price;
    std::string m_issue_date;
    std::string m_expire_date;
    std::string m_keywords;
    std::string m_origin;
    std::string m_region;
    std::string m_description;
public:
    IRInfo();
    ~IRInfo();

    friend DocumentPtr toJson(IRInfoPtr &info);
    friend bool fromJson(DocumentPtr &ptree, IRInfoPtr &info);
    friend std::string toJsonString(IRInfoPtr &info);
    friend bool fromJsonString(std::string json, IRInfoPtr &info);
};

#endif /* __IRINFO_HPP__ */
