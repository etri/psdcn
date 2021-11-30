/*
 * pubsub.cpp
 *
 * PubSub APIs
 */

#include "pubsub.hpp"
#include "logging.hpp"
#include "pskcmd.hpp"
#include <ndn-cxx/util/logging.hpp>
#include <rapidjson/document.h>

#include <iostream>
#include <map>
#include <vector>

using namespace std;

// module name for logging
NDN_LOG_INIT(psdcn.pubsub);

Pubsub::Pubsub(FacePtr face)
    : m_face(face)
    , m_prefix("/etri/rn")
{
}

Pubsub::Pubsub(FacePtr face, InterestOption option)
    : m_face(face)
    , m_prefix("/etri/rn")
    , m_option(option)
{
}

Pubsub::Pubsub(FacePtr face, string prefix)
    : m_face(face)
    , m_prefix(prefix)
{
}

Pubsub::Pubsub(FacePtr face, string prefix, InterestOption option)
    : m_face(face)
    , m_prefix(prefix)
    , m_option(option)
{
}

static string __OK = "OK";

void Pubsub::set_pub_prefix(const string prefix)
{
    m_pub_prefix = prefix;
}

bool Pubsub::pubadv(string dataname, 
    function<void(const string)> &onSuccess,
    function<void(const string, const string)> &onFailure,
    const string params) 
{
    DocumentPtr option = make_shared<rapidjson::Document>(rapidjson::kObjectType);
    option->Parse(params.c_str());
    PubAdvInfoPtr painfo = make_shared<PubAdvInfo>();
    bool parsed = fromJson(option, painfo);
    if (!parsed) {
        onFailure(dataname, "Invalid pubadv options");
        return false;
    }
    if (option->HasMember("storageprefix")) {
        string storageprefix = painfo->m_storageprefix;
        StorageType storagetype = StorageType(painfo->m_storagetype);
        if (storagetype == BROKER) {
            onFailure(dataname, "Storagetype not PUBLISHER or DIFS given " + storageprefix);
            return false;
        }
        painfo->m_storagetype = storagetype;
        painfo->m_storageprefix = storageprefix;
    }

    function<void (const Interest &, const Data &)> dataHandler = 
    [=](const Interest &interest, const Data &data) {
        const Block &_content = data.getContent();
        string content((const char *)_content.value(), (size_t)_content.value_size());  

        NDN_LOG_DEBUG_SS("PubAdv response " << content);
        DocumentPtr content_json = make_shared<rapidjson::Document>(rapidjson::kObjectType);
        content_json->Parse(content.c_str());
        if (content_json->HasMember("status") && 
                (__OK.compare((*content_json)["status"].GetString()) == 0)) {
            onSuccess(dataname);
        }
        else {
            const string reason = (*content_json)["reason"].GetString();
            onFailure(dataname, reason);
        }
    };
    function<void (const Interest &, const lp::Nack &)> nackHandler = 
    [=](const Interest &interest, const lp::Nack &nack) {
        onFailure(dataname, "Unreachable");
    };
    function<void (const Interest &)> timeoutHandler=
    [=](const Interest &interest) {
        onFailure(dataname, "Timeout");
    };

    InterestPtr interest = PSKCmd(m_option).make_pubadv(m_prefix, dataname, painfo, nullptr);
    NDN_LOG_DEBUG(*interest);

    m_face->expressInterest(*interest, dataHandler, nackHandler, timeoutHandler);
    return true;
}

bool Pubsub::pubunadv(string dataname, 
    function<void(const string)> &onSuccess,
    function<void(const string, const string)> &onFailure,
    const string params) 
{
    DocumentPtr option = make_shared<rapidjson::Document>(rapidjson::kObjectType);
    option->Parse(params.c_str());
    PubAdvInfoPtr painfo = make_shared<PubAdvInfo>();
    bool parsed = fromJson(option, painfo);
    if (!parsed) {
        onFailure(dataname, "Invalid pubunadv options");
        return false;
    }

    function<void (const Interest &, const Data &)> dataHandler = 
    [dataname, option, onSuccess, onFailure](const Interest &interest, const Data &data) {
        const Block &_content = data.getContent();
        string content((const char *)_content.value(), (size_t)_content.value_size());  

        NDN_LOG_DEBUG_SS("PubUnadv response " << content);
        DocumentPtr content_json = make_shared<rapidjson::Document>(rapidjson::kObjectType);
        content_json->Parse(content.c_str());
        if (content_json->HasMember("status") &&
                (__OK.compare((*content_json)["status"].GetString()) == 0)) {
            onSuccess(dataname);
        }
        else if (option->HasMember("allow_undefined") &&
                (*option)["allow_undefined"].GetBool() == true) {
            onSuccess(dataname);
        }
        else {
            const string reason = (*content_json)["reason"].GetString();
            onFailure(dataname, reason);
        }
        onSuccess(dataname);
    };
    function<void (const Interest &, const lp::Nack &)> nackHandler = 
    [dataname, onFailure](const Interest &interest, const lp::Nack &nack) {
        onFailure(dataname, "Unreachable");
    };
    function<void (const Interest &)> timeoutHandler=
    [dataname, onFailure](const Interest &interest) {
        onFailure(dataname, "Timeout");
    };

    InterestPtr interest = PSKCmd(m_option).make_pubunadv(m_prefix, dataname, painfo);
    NDN_LOG_DEBUG(*interest);

    m_face->expressInterest(*interest, dataHandler, nackHandler, timeoutHandler);
    return true;
}

bool Pubsub::pubdata(const string dataname, const long seq, const string item,
    function<void(const string, const long)> &onSuccess,
    function<void(const string, const long, const string)> &onFailure) 
{
    function<void(const Name &, const string &)> onRegisterFailed;
    function<void(const InterestFilter&, const Interest&)> dataPublisher;
    function<void(const Interest &, const Data &)> dataHandler;
    function<void(const Interest &, const lp::Nack &)> nackHandler;
    function<void(const Interest &)> timeoutHandler;

    onRegisterFailed = [dataname, seq, onFailure](const Name& prefix, const string& reason) {
        onFailure(dataname, seq, reason);
    };

    dataPublisher = [=](const InterestFilter& interestFilter, const Interest& interest) {
        // create data packet
        shared_ptr<Data> data = make_shared<Data>(interest.getName());
        data->setFreshnessPeriod(1_s);
        data->setContent(reinterpret_cast<const uint8_t*>(item.data()), item.size());
        KeyChain keyChain;
        keyChain.sign(*data);
        // return data packet to the requester
        m_face->put(*data);
        // unregister route for name
        m_face->setInterestFilter(interestFilter, nullptr, nullptr);
    };

    dataHandler = 
    [dataname, seq, onSuccess, onFailure](const Interest &interest, const Data &data) {
        const Block &_content = data.getContent();
        string content((const char *)_content.value(), (size_t)_content.value_size());  

        NDN_LOG_DEBUG_SS("PubData response " << content);
        DocumentPtr content_json = make_shared<rapidjson::Document>(rapidjson::kObjectType);
        content_json->Parse(content.c_str());
        string reason = "Unknwon pubdata error";
        bool success = false;
        if (content_json->HasMember("status")) {
            if (__OK.compare((*content_json)["status"].GetString()) == 0) {
                if ((*content_json)["value"].GetInt() == 1)
                    success = true;
                else if (content_json->HasMember("reason"))
                    reason = (*content_json)["reason"].GetString();
            }
        }
        if (success)
            onSuccess(dataname, seq);
        else
            onFailure(dataname, seq, reason);
    };
    nackHandler = [dataname, seq, onFailure](const Interest &interest, const lp::Nack &nack) {
        onFailure(dataname, seq, "Unreachable");
    };
    timeoutHandler = [dataname, seq, onFailure](const Interest &interest) {
        onFailure(dataname, seq, "Timeout");
    };

    // delivey data to applicationparameter
    PubDataInfoPtr pdinfo = make_shared<PubDataInfo>();
    pdinfo->m_data_prefix = dataname;
    pdinfo->m_data_sseq = seq;
    pdinfo->m_data_eseq = seq;
    pdinfo->m_pub_prefix = m_pub_prefix;

    Name name(dataname);
    InterestFilter interestFilter(name);
    m_face->setInterestFilter(interestFilter, dataPublisher, onRegisterFailed);

    InterestPtr interest = PSKCmd(m_option).make_pubdata(m_prefix, dataname, seq, pdinfo);
    NDN_LOG_DEBUG(*interest);

    m_face->expressInterest(*interest, dataHandler, nackHandler, timeoutHandler);
    return true;
}

bool Pubsub::subtopic(const string topicname, 
    function<void(const string,
                  const map<string, vector<string> >)> &onSuccess,
    function<void(const string, const string)> &onFailure,
    const string params) 
{
    DocumentPtr option = make_shared<rapidjson::Document>(rapidjson::kObjectType);
    option->Parse(params.c_str());
    SubInfoPtr stinfo = make_shared<SubInfo>();
    bool parsed = fromJson(option, stinfo);
    if (!parsed) {
        onFailure(topicname, "Invalid subtopic options");
        return false;
    }

    function<void (const Interest &, const Data &)> dataHandler = 
    [=](const Interest &interest, const Data &data) {
        const Block &_content = data.getContent();
        string content((const char *)_content.value(), (size_t)_content.value_size());  
        NDN_LOG_DEBUG_SS("SubTopic response " << content);
        DocumentPtr content_json = make_shared<rapidjson::Document>(rapidjson::kObjectType);
        content_json->Parse(content.c_str());
        if (content_json->HasMember("status") && 
                (__OK.compare((*content_json)["status"].GetString()) == 0)) {

            const rapidjson::Value &value = (*content_json)["value"];
            map<string, vector<string> > entries;
            for (rapidjson::Value::ConstValueIterator iter = value.Begin();
                    iter != value.End();
                    ++iter) {
                const rapidjson::Value &item = *iter;
                string dataname = item[0].GetString();

                const rapidjson::Value &rns = item[1];
                for (rapidjson::Value::ConstValueIterator rns_iter = rns.Begin();
                    rns_iter != rns.End();
                    ++rns_iter) {
                    const rapidjson::Value &rn_name = *rns_iter;
                    string rnname = rn_name.GetString();
                    entries[dataname].push_back(rnname);  // collect entries
                }
            }
            onSuccess(topicname, entries);
        }
        else {
            string reason = "Unknwon pubdata error";
            if (content_json->HasMember("reason"))
                reason = (*content_json)["reason"].GetString();
            onFailure(topicname, reason);
        }
    };
    function<void (const Interest &, const lp::Nack &)> nackHandler = 
    [=](const Interest &interest, const lp::Nack &nack) {
        onFailure(topicname, "Unreachable");
    };
    function<void (const Interest &)> timeoutHandler=
    [=](const Interest &interest) {
        onFailure(topicname, "Timeout");
    };

    InterestPtr interest = PSKCmd(m_option).make_subtopic(m_prefix, topicname, stinfo);
    NDN_LOG_DEBUG(*interest);

    m_face->expressInterest(*interest, dataHandler, nackHandler, timeoutHandler);
    return true;
}

bool Pubsub::submani(const string dataname, const string rn_name,
    function<void(const string, const DataManifest)> &onSuccess,
    function<void(const string, const string)> &onFailure)
{
    SubInfoPtr sminfo = make_shared<SubInfo>();

    function<void (const Interest &, const Data &)> dataHandler = 
    [dataname, rn_name, onSuccess, onFailure](const Interest &interest, const Data &data) {
        const Block &_content = data.getContent();
        string content((const char *)_content.value(), (size_t)_content.value_size());  
        NDN_LOG_DEBUG_SS("SubMani response " << content);
        DocumentPtr content_json = make_shared<rapidjson::Document>(rapidjson::kObjectType);
        content_json->Parse(content.c_str());
        if (content_json->HasMember("status") && 
                (__OK.compare((*content_json)["status"].GetString()) == 0)) {
            DataManifest manifest(rn_name,
                (*content_json)["fst"].GetInt(),
                (*content_json)["lst"].GetInt());
            onSuccess(dataname, manifest);
        }
        else if (content_json->HasMember("reason"))
            onFailure(dataname, (*content_json)["reason"].GetString());
    };
    function<void (const Interest &, const lp::Nack &)> nackHandler = 
    [=](const Interest &interest, const lp::Nack &nack) {
        onFailure(dataname, "Unreachable");
    };
    function<void (const Interest &)> timeoutHandler=
    [=](const Interest &interest) {
        onFailure(dataname, "Timeout");
    };

    InterestPtr interest = PSKCmd(m_option).make_submani(rn_name, m_prefix, dataname, sminfo);
    NDN_LOG_DEBUG(*interest);
    m_face->expressInterest(*interest, dataHandler, nackHandler, timeoutHandler);
    return true;
}

bool Pubsub::sublocal(const std::string topicname,
    std::function<void(/*topicname*/const std::string,
                       /*broker*/const std::string,
                       const std::vector<LocalManifest>)> &onSuccess,
    std::function<void(/*topicname*/const std::string, /*reason*/const std::string)> &onFailure,
    const string params) 
{
    DocumentPtr option = make_shared<rapidjson::Document>(rapidjson::kObjectType);
    option->Parse(params.c_str());
    SubInfoPtr slinfo = make_shared<SubInfo>();
    bool parsed = fromJson(option, slinfo);
    if (!parsed) {
        onFailure(topicname, "Invalid sublocal options");
        return false;
    }

    function<void (const Interest &, const Data &)> dataHandler = 
    [topicname, onSuccess, onFailure](const Interest &interest, const Data &data) {
        const Block &_content = data.getContent();
        string content((const char *)_content.value(), (size_t)_content.value_size());  
        NDN_LOG_DEBUG_SS("SubLocal response " << content);
        DocumentPtr content_json = make_shared<rapidjson::Document>(rapidjson::kObjectType);
        content_json->Parse(content.c_str());
        if (content_json->HasMember("status") && 
                (__OK.compare((*content_json)["status"].GetString()) != 0)) {
            const string reason = content_json->HasMember("reason")?
                (*content_json)["reason"].GetString(): "No matches found";
            onFailure(topicname, reason);
            return;
        }
	// Copy value part of the content to a new Document
        DocumentPtr value_json = make_shared<rapidjson::Document>(rapidjson::kObjectType);
        // value_json->Swap((*content_json)["value"]);
        value_json->CopyFrom((*content_json)["value"], value_json->GetAllocator());
        const string broker = (*value_json)["broker"].GetString();
        NDN_LOG_DEBUG_SS("sublocal broker " << broker);
        const rapidjson::Value &manifests = (*value_json)["manifests"].GetArray();
        vector<LocalManifest> entries;
        for (rapidjson::Value::ConstValueIterator iter = manifests.Begin();
                iter != manifests.End();
                ++iter) {
            const auto manifest = (*iter).GetArray();
            entries.push_back(
                LocalManifest(manifest[0].GetString(), manifest[1].GetInt(), manifest[2].GetInt()));
        }
        onSuccess(topicname, broker, entries);
    };
    function<void (const Interest &, const lp::Nack &)> nackHandler = 
    [=](const Interest &interest, const lp::Nack &nack) {
        onFailure(topicname, "Unreachable");
    };
    function<void (const Interest &)> timeoutHandler=
    [=](const Interest &interest) {
        onFailure(topicname, "Timeout");
    };

    InterestPtr interest = PSKCmd(m_option).make_sublocal(m_prefix, topicname, slinfo);
    NDN_LOG_DEBUG(*interest);

    m_face->expressInterest(*interest, dataHandler, nackHandler, timeoutHandler);
    return true;
}
