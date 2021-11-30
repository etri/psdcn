/*
 * example for publish
 */

#include <ndn-cxx/util/logging.hpp>
#include <boost/asio/io_service.hpp>

// user defined include files
#include "pubsub.hpp"
#include "pskcmd.hpp"
#include "logging.hpp"

#include <iostream>
#include <map>
#include <vector>

// module name for logging
NDN_LOG_INIT(psdcn.sub-demo);

using namespace ndn;
using namespace std;
using PubsubPtr = shared_ptr<Pubsub>;

FacePtr gFace = nullptr;

void request_data(PubsubPtr ps, string prefix, string dataname, long seq)
{
    function<void(const Interest &, const Data &)> dataHandler;
    function<void(const Interest &, const lp::Nack &)> nackHandler;
    function<void(const Interest &)> timeoutHandler;

    dataHandler = [=](const Interest &interest, const Data &data) {
        NDN_LOG_INFO_SS("SubData request: " << interest);
        const Block &content = data.getContent();
        string value((const char *)content.value(), (size_t)content.value_size());
        NDN_LOG_INFO_SS("SubData content: " << value);
    };
    nackHandler = [=](const Interest &interest, const lp::Nack &nack) {
        const Name &name = nack.getInterest().getName();
        NDN_LOG_INFO_SS("SubData Nack: " << name << ", reason: " << nack.getReason());
    };
    timeoutHandler = [=](const Interest &interest) {
        NDN_LOG_INFO_SS("SubData Timeout: " << dataname);
    };

    InterestPtr interest = PSKCmd(ps->m_option).make_subdata(ps->m_prefix, dataname, seq);
    ps->m_face->expressInterest(*interest, dataHandler, nackHandler, timeoutHandler);
}

void request_manifest(PubsubPtr ps, const string dataname, const string rn_name)
{
    function<void (const string, const DataManifest)> subSuccess =
    [=](const string topicname, const DataManifest manifest) {
        NDN_LOG_INFO_SS("Dataname: " << dataname << ", Manifest: (" 
            << manifest.rn_name << " " << manifest.fst << "-" << manifest.lst << ")");
        request_data(ps, manifest.rn_name, dataname, manifest.lst);
        cout << endl;
    };
    function<void (const string, const string)> subFailure =
    [=](const string topicname, const string reason) {
        NDN_LOG_INFO_SS("Failed to fetch manifest of " << dataname << ", reason: " << reason);
    };
    ps->submani(dataname, rn_name, subSuccess, subFailure);
}

void subscribe_example(PubsubPtr ps, const string topicname)
{
    function<void (const string, const map<string, vector<string> >)> subSuccess =
    [=](const string topicname, const map<string, vector<string> > entries) {
        cout << endl;
        for (auto iter : entries)
            request_manifest(ps, iter.first, iter.second.back());  // consider last one only
    };
    function<void (const string, const string)> subFailure =
    [=](const string topicname, const string reason) {
        NDN_LOG_INFO_SS("Failed to subscribe to " << topicname << ", reason: " << reason);
    };
    ps->subtopic(topicname, subSuccess, subFailure);
}

void sublocal_example(PubsubPtr ps, const string topicname)
{
    function<void (const string, const string, const vector<LocalManifest>)> subSuccess =
    [=](const string topicname, const string broker, const vector<LocalManifest> entries) {
        cout << endl;
        for (auto iter : entries)
            request_data(ps, broker, iter.dataname, iter.lst);
    };
    function<void (const string, const string)> subFailure =
    [=](const string topicname, const string reason) {
        NDN_LOG_INFO_SS("Failed to subscribe to " << topicname << ", reason: " << reason);
    };
    ps->sublocal(topicname, subSuccess, subFailure);
}

int main(int argc, char *argv[])
{
    auto gIOService = make_shared<boost::asio::io_service>();
    auto gFace = make_shared<Face>(*gIOService);
    const string svc_name = "/dcn/psdcn";
    auto ps = make_shared<Pubsub>(gFace, svc_name);

    if (argc == 1)
        subscribe_example(ps, "/etri/#");
    else
        sublocal_example(ps, "/etri/#");

    try {
        gFace->processEvents();
    } catch (std::exception &e) {
        NDN_LOG_ERROR(e.what());
    }

    ::ndn::util::Logging::flush();

    return 0;
}
