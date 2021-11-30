/*
 * pubsub.hpp
 *
 * PubSub APIs
 */

#ifndef __PUBSUB_HPP__
#define __PUBSUB_HPP__

#include <memory>

/*
#include <ndn-cxx/interest.hpp>
#include <ndn-cxx/face.hpp>

#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
*/

#include "interestoption.hpp"
#include "pubadvinfo.hpp"
#include "pubdatainfo.hpp"
#include "irinfo.hpp"
#include "subinfo.hpp"

using namespace ndn;

/*
using FacePtr = std::shared_ptr<Face>;
using InterestPtr = std::shared_ptr<Interest>;

namespace PTree = boost::property_tree;
namespace PTreeJson = boost::property_tree::json_parser;

using PTreePtr = std::shared_ptr<PTree::ptree>;
*/

struct DataManifest {
    std::string rn_name;
    uint32_t fst;
    uint32_t lst;

    DataManifest(std::string _rn_name, uint32_t _fst, uint32_t _lst):
        rn_name(_rn_name),
        fst(_fst),
        lst(_lst)
    {}
};

struct LocalManifest {
    std::string dataname;
    uint32_t fst;
    uint32_t lst;

    LocalManifest(std::string _dataname, uint32_t _fst, uint32_t _lst):
        dataname(_dataname),
        fst(_fst),
        lst(_lst)
    {}
};

class Pubsub {
public:
    FacePtr m_face;
    std::string m_prefix;
    std::string m_pub_prefix;

    InterestOption m_option;

public:
    Pubsub(FacePtr face);
    Pubsub(FacePtr face, InterestOption option);
    Pubsub(FacePtr face, std::string prefix);
    Pubsub(FacePtr face, std::string prefix, InterestOption option);

    void set_pub_prefix(const std::string);

    bool pubadv(const std::string dataname, 
        std::function<void(/*dataname*/const std::string)> &onSuccess,
        std::function<void(/*dataname*/const std::string, /*reason*/const std::string)> &onFailure,
        const std::string params = "{}");

    bool pubunadv(const std::string dataname, 
        std::function<void(/*dataname*/const std::string)> &onSuccess,
        std::function<void(/*dataname*/const std::string, /*reason*/const std::string)> &onFailure,
        const std::string params = "{}");

    bool pubdata(const std::string dataname, const long seq, const std::string item,
        std::function<void(/*dataname*/const std::string, /*seq*/const long)> &onSuccess,
        std::function<void(/*dataname*/const std::string, /*seq*/const long,
		                                          const /*reason*/std::string)> &onFailure);

    bool subtopic(const std::string topicname,
        std::function<void(/*topicname*/const std::string,
                           const std::map</*dataname*/std::string,
                                          /*rn_names*/std::vector<std::string> >)> &onSuccess,
        std::function<void(/*topicname*/const std::string, /*reason*/const std::string)> &onFailure,
        const std::string params = "{}");

    bool submani(const std::string dataname,
        const std::string rn_name,
        std::function<void(/*dataname*/const std::string, const DataManifest)> &onSuccess,
        std::function<void(/*dataname*/const std::string, /*reason*/const std::string)> &onFailure);

    bool sublocal(const std::string topicname,
        std::function<void(/*topicname*/const std::string,
                           /*broker*/const std::string,
                           const std::vector<LocalManifest>)> &onSuccess,
        std::function<void(/*topicname*/const std::string, /*reason*/const std::string)> &onFailure,
        const std::string params = "{}");

    // static ssize_t findParametersDigestComponent(const Name &name);
};

#endif /* __PUBSUB_HPP_ */
