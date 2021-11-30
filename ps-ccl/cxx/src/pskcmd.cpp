/*
 * pskcmd.cpp
 *
 * make interest packet
 */

#include "pskcmd.hpp"
#include "logging.hpp"
#include "pubadvinfo.hpp"

// module name for logging
NDN_LOG_INIT(psdcn.pskcmd);

PSKCmd::PSKCmd(InterestOption option)
    : m_option(option)
{
}

InterestPtr PSKCmd::make_interest(Name name, DocumentPtr params)
{
    InterestPtr interest = nullptr;
    interest = std::make_shared<ndn::Interest>(name);
    interest->setCanBePrefix(m_option.m_canBePrefix);
    interest->setMustBeFresh(m_option.m_mustBeFresh);
    interest->setInterestLifetime(time::milliseconds(m_option.m_lifetime));
    if (m_option.m_nonce.has_value())
        interest->setNonce(*m_option.m_nonce);
    if (m_option.m_hopLimit.has_value())
        interest->setHopLimit(*m_option.m_hopLimit);

    std::stringstream ss;
    if (params != nullptr) {
        rapidjson::StringBuffer buffer;
        rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
        params->Accept(writer);
        ss << buffer.GetString();
        std::string json = ss.str();
        NDN_LOG_DEBUG_SS(json);
        Block parameters = makeStringBlock(tlv::ApplicationParameters, ss.str());
        interest->setApplicationParameters(parameters);
    }
    return interest;
}

InterestPtr PSKCmd::make_pubadv(std::string prefix, std::string dataname,
    PubAdvInfoPtr advinfo, IRInfoPtr irinfo)
{
    InterestPtr interest = nullptr;
    ndn::Name name(prefix);
    name.append("PA");
    name.append(dataname);

    if (advinfo == nullptr)
        advinfo = std::make_shared<PubAdvInfo>();

    DocumentPtr advtree = toJson(advinfo);
    DocumentPtr irtree = toJson(irinfo);
    DocumentPtr params = std::make_shared<rapidjson::Document>(rapidjson::kObjectType);
    params->SetObject();

    if (advtree == nullptr) {
        rapidjson::Value nullnode(rapidjson::kObjectType);
        nullnode.SetNull();
        params->AddMember("pubadvinfo", nullnode, params->GetAllocator());
    } else
        params->AddMember("pubadvinfo", *advtree, params->GetAllocator());

    if (irtree == nullptr) {
        rapidjson::Value nullnode(rapidjson::kObjectType);
        nullnode.SetNull();
        params->AddMember("irinfo", nullnode, params->GetAllocator());
    } else
        params->AddMember("irinfo", *irtree, params->GetAllocator());

    interest = make_interest(name, params);
    return interest;
}

InterestPtr PSKCmd::make_pubunadv(std::string prefix, std::string dataname,
    PubAdvInfoPtr advinfo)
{
    InterestPtr interest = nullptr;
    ndn::Name name(prefix);
    name.append("PU");
    name.append(dataname);

    DocumentPtr advtree = toJson(advinfo);
    DocumentPtr params = std::make_shared<rapidjson::Document>(rapidjson::kObjectType);
    if (advtree == nullptr) {
        rapidjson::Value nullnode(rapidjson::kObjectType);
        nullnode.SetNull();
        params->AddMember("pubadvinfo", nullnode, params->GetAllocator());
    } else
        params->AddMember("pubadvinfo", *advtree, params->GetAllocator());

    interest = make_interest(name, params);
    return interest;
}

InterestPtr PSKCmd::make_pubdata(std::string prefix, std::string dataname, long sequence,
    PubDataInfoPtr datainfo)
{
    InterestPtr interest = nullptr;
    ndn::Name name(prefix);
    name.append("PD");
    name.append(dataname);
    name.append(std::to_string(sequence));

    DocumentPtr datatree = toJson(datainfo);
    DocumentPtr params = std::make_shared<rapidjson::Document>(rapidjson::kObjectType);
    if (datatree == nullptr) {
        rapidjson::Value nullnode(rapidjson::kObjectType);
        nullnode.SetNull();
        params->AddMember("pubdatainfo", nullnode, params->GetAllocator());
    } else
        params->AddMember("pubdatainfo", *datatree, params->GetAllocator());

    return make_interest(name, params);
}

InterestPtr PSKCmd::make_subtopic(std::string prefix, std::string topicname,
    SubInfoPtr subinfo)
{
    InterestPtr interest = nullptr;
    ndn::Name name(prefix);
    name.append("ST");
    name.append(topicname);

    DocumentPtr subtree = toJson(subinfo);
    DocumentPtr params = std::make_shared<rapidjson::Document>(rapidjson::kObjectType);
    if (subtree == nullptr) {
        rapidjson::Value nullnode(rapidjson::kObjectType);
        nullnode.SetNull();
        params->AddMember("subinfo", nullnode, params->GetAllocator());
    } else
        params->AddMember("subinfo", *subtree, params->GetAllocator());

    return make_interest(name, params);
}

InterestPtr PSKCmd::make_submani(std::string prefix,
    std::string m_prefix, std::string dataname, SubInfoPtr subinfo)
{
    InterestPtr interest = nullptr;
    ndn::Name name(m_prefix);
    name.append("SM");
    name.append(dataname);

    DocumentPtr subtree = toJson(subinfo);
    DocumentPtr params = std::make_shared<rapidjson::Document>(rapidjson::kObjectType);
    if (subtree == nullptr) {
        rapidjson::Value nullnode(rapidjson::kObjectType);
        nullnode.SetNull();
        params->AddMember("subinfo", nullnode, params->GetAllocator());
    } else
        params->AddMember("subinfo", *subtree, params->GetAllocator());

    interest = make_interest(name, params);
    // Forwarding hint
    ndn::DelegationList fwd_hint = interest->getForwardingHint();
    fwd_hint.insert(1, ndn::Name(prefix));
    interest->setForwardingHint(fwd_hint);
    return interest;
}

InterestPtr PSKCmd::make_sublocal(std::string prefix, std::string topicname,
    SubInfoPtr subinfo)
{
    InterestPtr interest = nullptr;
    ndn::Name name(prefix);
    name.append("SL");
    name.append(topicname);

    DocumentPtr subtree = toJson(subinfo);
    DocumentPtr params = std::make_shared<rapidjson::Document>(rapidjson::kObjectType);
    if (subtree == nullptr) {
        rapidjson::Value nullnode(rapidjson::kObjectType);
        nullnode.SetNull();
        params->AddMember("subinfo", nullnode, params->GetAllocator());
    } else
        params->AddMember("subinfo", *subtree, params->GetAllocator());

    return make_interest(name, params);
}

InterestPtr PSKCmd::make_subdata(std::string prefix, std::string dataname, long sequence)
{
    ndn::Name name(dataname);
    name.append(std::to_string(sequence));

    InterestPtr interest = make_interest(name, nullptr);
    interest->setMustBeFresh(false);  // Should be opposite of that for pub* related commands
    interest->setCanBePrefix(true);   // Caching for dual CS enablement
    // Forwarding hint
    ndn::DelegationList fwd_hint = interest->getForwardingHint();
    fwd_hint.insert(1, ndn::Name(prefix));
    interest->setForwardingHint(fwd_hint);
    return interest;
}
