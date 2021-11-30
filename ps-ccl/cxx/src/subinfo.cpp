/*
 * subinfo.cpp
 *
 * SubInfo class
 */

#include "subinfo.hpp"

SubInfo::SubInfo()
    : m_topicscope(0)
{
}

SubInfo::~SubInfo()
{
}

DocumentPtr toJson(SubInfoPtr &info)
{
    if(info == nullptr)
        return nullptr;

    DocumentPtr document = std::make_shared<rapidjson::Document>();
    document->SetObject();

    rapidjson::Value topicscope(info->m_topicscope);
    document->AddMember("topicscope", topicscope, document->GetAllocator());

    rapidjson::Value servicetoken(info->m_servicetoken.c_str(), info->m_servicetoken.size());
    document->AddMember("servicetoken", servicetoken, document->GetAllocator());

    return document;
}

bool fromJson(DocumentPtr &document, SubInfoPtr &info)
{
    if(document == nullptr)
        return false;
    if(info == nullptr)
        return false;

    if(document->HasMember("topicscope"))
        info->m_topicscope = (*document)["topicscope"].GetInt();
    else
        info->m_topicscope = 0;

    if(document->HasMember("servicetoken"))
        info->m_servicetoken = (*document)["servicetoken"].GetString();
    else
        info->m_servicetoken.clear();

    return true;
}

std::string toJsonString(SubInfoPtr &info)
{
    std::stringstream ss;

    if(info == nullptr)
        return ss.str();

    DocumentPtr document = toJson(info);
    if(document == nullptr)
        return ss.str();

    rapidjson::StringBuffer buffer;
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);

    document->Accept(writer);

    ss << buffer.GetString();

    return ss.str();
}

bool fromJsonString(std::string json, SubInfoPtr &info)
{
    DocumentPtr document = std::make_shared<rapidjson::Document>();
    document->Parse(json.c_str());

    return fromJson(document, info);
}
