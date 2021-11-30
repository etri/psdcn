/*
 * irinfo.cpp
 *
 * irinfo
 */

#include "irinfo.hpp"

IRInfo::IRInfo()
    : m_price(0.0)
{
}
IRInfo::~IRInfo()
{
}

DocumentPtr toJson(IRInfoPtr &info)
{
    if(info == nullptr) {
        return nullptr;
    }

    DocumentPtr document = std::make_shared<rapidjson::Document>();
    document->SetObject();

    rapidjson::Value id(info->m_id.c_str(), info->m_id.size());
    document->AddMember("id", id, document->GetAllocator());

    rapidjson::Value name(info->m_name.c_str(), info->m_name.size());
    document->AddMember("name", name, document->GetAllocator());

    rapidjson::Value providerid(info->m_providerid.c_str(), info->m_providerid.size());
    document->AddMember("providerid", providerid, document->GetAllocator());

    rapidjson::Value price(info->m_price);
    document->AddMember("price", price, document->GetAllocator());

    rapidjson::Value issue_date(info->m_issue_date.c_str(), info->m_issue_date.size());
    document->AddMember("issue_date", issue_date, document->GetAllocator());

    rapidjson::Value expire_date(info->m_expire_date.c_str(), info->m_expire_date.size());
    document->AddMember("expire_date", expire_date, document->GetAllocator());

    rapidjson::Value keywords(info->m_keywords.c_str(), info->m_keywords.size());
    document->AddMember("keywords", keywords, document->GetAllocator());

    rapidjson::Value origin(info->m_origin.c_str(), info->m_origin.size());
    document->AddMember("origin", origin, document->GetAllocator());

    rapidjson::Value region(info->m_region.c_str(), info->m_region.size());
    document->AddMember("region", region, document->GetAllocator());

    rapidjson::Value description(info->m_description.c_str(), info->m_description.size());
    document->AddMember("description", description, document->GetAllocator());

    return document;
}

bool fromJson(DocumentPtr &document, IRInfoPtr &info)
{
    if(document == nullptr)
        return false;
    if(info == nullptr)
        return false;

    if((*document)["id"].IsNull())
        info->m_id.clear();
    else
        info->m_id = (*document)["id"].GetString();

    if((*document)["name"].IsNull())
        info->m_name.clear();
    else
        info->m_name = (*document)["name"].GetString();

    if((*document)["providerid"].IsNull())
        info->m_providerid.clear();
    else
        info->m_providerid = (*document)["providerid"].GetString();

    if((*document)["price"].IsNull())
        info->m_price = 0.0;
    else
        info->m_price = (*document)["price"].GetFloat();

    if((*document)["issue_date"].IsNull())
        info->m_issue_date.clear();
    else
        info->m_issue_date = (*document)["issue_date"].GetString();

    if((*document)["expire_date"].IsNull())
        info->m_expire_date.clear();
    else
        info->m_expire_date = (*document)["expire_date"].GetString();

    if((*document)["keywords"].IsNull())
        info->m_keywords.clear();
    else
        info->m_keywords = (*document)["keywords"].GetString();

    if((*document)["origin"].IsNull())
        info->m_origin.clear();
    else
        info->m_origin = (*document)["origin"].GetString();

    if((*document)["region"].IsNull())
        info->m_region.clear();
    else
        info->m_region = (*document)["region"].GetString();

    if((*document)["description"].IsNull())
        info->m_description.clear();
    else
        info->m_description = (*document)["description"].GetString();

    return true;
}

std::string toJsonString(IRInfoPtr &info)
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

bool fromJsonString(std::string json, IRInfoPtr &info)
{
    DocumentPtr document = std::make_shared<rapidjson::Document>();
    document->Parse(json.c_str());

    return fromJson(document, info);
}
