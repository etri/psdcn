/*
 * pubadvinfo.cpp
 *
 * PubAdvInfo class
 */
#include "pubadvinfo.hpp"

PubAdvInfo::PubAdvInfo()
    : m_storagetype(0)
    , m_topicscope(0)
    , m_startseq(1)
    , m_redefine(false)
    , m_maxdatapktcnt(100)
{
}
PubAdvInfo::~PubAdvInfo()
{
}

DocumentPtr toJson(PubAdvInfoPtr &info)
{
    if(info == nullptr)
        return nullptr;

    DocumentPtr document = std::make_shared<rapidjson::Document>();
    document->SetObject();

    rapidjson::Value storagetype(info->m_storagetype);
    document->AddMember("storagetype", storagetype, document->GetAllocator());

    rapidjson::Value storageprefix(info->m_storageprefix.c_str(), info->m_storageprefix.size());
    document->AddMember("storageprefix", storageprefix, document->GetAllocator());

    rapidjson::Value dataname(info->m_dataname.c_str(), info->m_dataname.size());
    document->AddMember("dataname", dataname, document->GetAllocator());

    rapidjson::Value topicscope(info->m_topicscope);
    document->AddMember("topicscope", topicscope, document->GetAllocator());

    rapidjson::Value startseq(info->m_startseq);
    document->AddMember("startseq", startseq, document->GetAllocator());

    rapidjson::Value redefine(info->m_redefine);
    document->AddMember("redefine", redefine, document->GetAllocator());

    rapidjson::Value actionexceeddatapktcnt(info->m_actionexceeddatapktcnt.c_str(),
        info->m_actionexceeddatapktcnt.size());
    document->AddMember("actionexceeddatapktcnt", actionexceeddatapktcnt, document->GetAllocator());

    rapidjson::Value maxdatapktcnt(info->m_maxdatapktcnt);
    document->AddMember("maxdatapktcnt", maxdatapktcnt, document->GetAllocator());

    return document;
}

bool fromJson(DocumentPtr &document, PubAdvInfoPtr &info)
{
    if(document == nullptr)
        return false;
    if(info == nullptr)
        return false;

    if(document->HasMember("storagetype"))
        info->m_storagetype = (*document)["storagetype"].GetInt();
    else
        info->m_storagetype = 0;

    if(document->HasMember("storageprefix"))
        info->m_storageprefix = (*document)["storageprefix"].GetString();
    else
        info->m_storageprefix.clear();

    if(document->HasMember("topicscope"))
        info->m_topicscope = (*document)["topicscope"].GetInt();
    else
        info->m_topicscope = 0;

    if(document->HasMember("startseq"))
        info->m_startseq = (*document)["startseq"].GetInt64();
    else
        info->m_startseq = 0;

    if(document->HasMember("redefine"))
        info->m_redefine = (*document)["redefine"].GetBool();
    else
        info->m_redefine = false;

    if(document->HasMember("actionexceeddatapktcnt"))
        info->m_actionexceeddatapktcnt = (*document)["actionexceeddatapktcnt"].GetString();
    else
        info->m_actionexceeddatapktcnt.clear();

    if(document->HasMember("maxdatapktcnt"))
        info->m_maxdatapktcnt = (*document)["maxdatapktcnt"].GetInt64();
    else
        info->m_maxdatapktcnt = 0;

    return true;
}

std::string toJsonString(PubAdvInfoPtr &info)
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

bool fromJsonString(std::string json, PubAdvInfoPtr &info)
{
    DocumentPtr document = std::make_shared<rapidjson::Document>();
    document->Parse(json.c_str());

    return fromJson(document, info);
}
