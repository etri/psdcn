/*
 * example for publish
 */

#include <ndn-cxx/util/logging.hpp>
#include <boost/asio/io_service.hpp>

// user defined include files
#include "pubsub.hpp"
#include "logging.hpp"

// module name for logging
NDN_LOG_INIT(psdcn.pub-demo);

using namespace ndn;
using namespace std;

using PubsubPtr = shared_ptr<Pubsub>;

/** For easier tests, used static variables extensively */
void pubdata_example(PubsubPtr ps, const string dataname, long seq, const string item);

void publish_example(PubsubPtr ps,
    const string dataname, const string seq, const string item, const int topicscope=GLOBAL)
{
    function<void (const string)> advSuccess =
    [ps, seq, item](const string dataname) {
        NDN_LOG_INFO_SS("Advertised " << dataname);
        pubdata_example(ps, dataname, stoi(seq), item);
    };
    function<void (const string, const string)> advFailure =
    [ps, advSuccess](const string dataname, const string reason) {
        if (reason.compare("Redefine") == 0)
            advSuccess(dataname);
        else
            NDN_LOG_INFO_SS("Failed to advertise " << dataname << ": " << reason);
    };
    ps->pubadv(dataname, advSuccess, advFailure, topicscope==LOCAL? "{\"topicscope\": 1}": "{}");
}

void pubdata_example(PubsubPtr ps, const string dataname, long seq, const string item)
{
    function<void (const string, const long)> pubSuccess =
    [](const string dataname, const long seq) {
        NDN_LOG_INFO_SS("Published " << dataname << "/" << seq);
        exit(0);
    };
    function<void (const string, const long, const string)> pubFailure =
    [=](const string dataname, const long seq, const string reason) {
        NDN_LOG_INFO_SS("Failed to publish " << dataname << "/" << seq << ": " << reason);
        exit(1);
    };
    ps->pubdata(dataname, seq, item, pubSuccess, pubFailure);
}

int main(int argc, char *argv[])
{
    // shared_ptr<boost::asio::io_service> gIOService = make_shared<boost::asio::io_service>();
    auto gIOService = make_shared<boost::asio::io_service>();
    auto gFace = make_shared<Face>(*gIOService);
    const string svc_name = "/dcn/psdcn";

    auto ps = make_shared<Pubsub>(gFace, svc_name);
    if (argc > 2)
        ps->set_pub_prefix(argv[2]);
    const string seq = argc > 1? argv[1]: "1";

    if (string(argv[0]).compare("pubdemo") == 0) {
        // TopicScope.GLOBAL
        string hello = "Hello PSDCNv3 [" + seq + "]!";
        publish_example(ps, "/etri/test/global", seq, hello);
    }
    else {
        // TopicScope.LOCAL
        string holla = "Holla PSDCNv3 [" + seq + "]!";
        publish_example(ps, "/etri/test/local", seq, holla, LOCAL);
    }

    try {
        gFace->processEvents();
    } catch (std::exception &e) {
        NDN_LOG_ERROR(e.what());
    }
    ::ndn::util::Logging::flush();
    return 0;
}
