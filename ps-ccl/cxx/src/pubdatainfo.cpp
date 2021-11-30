/*
 * pubdatainfo.cpp
 *
 * PubDataInfo class
 */
#include "pubdatainfo.hpp"

PubDataInfo::PubDataInfo()
    : m_data_sseq(1)
    , m_data_eseq(1)
{
}
PubDataInfo::~PubDataInfo()
{
}

DocumentPtr toJson(PubDataInfoPtr &info)
{
    if(info == nullptr)
        return nullptr;

    DocumentPtr document = std::make_shared<rapidjson::Document>();
    document->SetObject();

    // rapidjson::Value data(info->m_data.c_str(), info->m_data.size());
    // document->AddMember("data", data, document->GetAllocator());

    rapidjson::Value data_prefix(info->m_data_prefix.c_str(), info->m_data_prefix.size());
    document->AddMember("data_prefix", data_prefix, document->GetAllocator());

    rapidjson::Value data_sseq(info->m_data_sseq);
    document->AddMember("data_sseq", data_sseq, document->GetAllocator());

    rapidjson::Value data_eseq(info->m_data_eseq);
    document->AddMember("data_eseq", data_eseq, document->GetAllocator());

    std::string pub_prefix = info->m_pub_prefix;
    if(pub_prefix.length() > 0) {
        rapidjson::Value pub_prefix(info->m_pub_prefix.c_str(), info->m_pub_prefix.size());
        document->AddMember("pub_prefix", pub_prefix, document->GetAllocator());
    }

    return document;
}

bool fromJson(DocumentPtr &document, PubDataInfoPtr &info)
{
    if(document == nullptr)
        return false;
    if(info == nullptr)
        return false;

    if((*document)["data_prefix"].IsNull())
        info->m_data_prefix = nullptr;
    else
        info->m_data_prefix = (*document)["data"].GetString();

    if((*document)["data_sseq"].IsNull())
        info->m_data_sseq = 1;
    else
        info->m_data_sseq = (*document)["data_sseq"].GetInt64();

    if((*document)["data_eseq"].IsNull())
        info->m_data_eseq = 1;
    else
        info->m_data_eseq = (*document)["data_eseq"].GetInt64();

    if(!(*document)["pub_prefix"].IsNull())
        info->m_pub_prefix = (*document)["pub_prefix"].GetString();

    return true;
}

std::string toJsonString(PubDataInfoPtr &info)
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

bool fromJsonString(std::string json, PubDataInfoPtr &info)
{
    DocumentPtr document = std::make_shared<rapidjson::Document>();
    document->Parse(json.c_str());

    return fromJson(document, info);
}
