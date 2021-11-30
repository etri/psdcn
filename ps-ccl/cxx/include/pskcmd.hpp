/*
 * pskcmd.hpp
 *
 * make interest packet 
 */

#ifndef __PSKCMD_HPP_
#define __PSKCMD_HPP_

//#include <ndn-cxx/interest.hpp>
//#include <ndn-cxx/face.hpp>

/*
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

class PSKCmd {
public:
    InterestOption m_option;

public:
    PSKCmd(InterestOption option);

    InterestPtr make_interest(Name name, DocumentPtr params);

    InterestPtr make_pubadv(std::string prefix, std::string dataname,
            PubAdvInfoPtr advinfo=nullptr, IRInfoPtr itinfo=nullptr);

    InterestPtr make_pubunadv(std::string prefix, std::string dataname,
            PubAdvInfoPtr advinfo=nullptr);

    InterestPtr make_pubdata(std::string prefix, std::string dataname, long sequence,
            PubDataInfoPtr datainfo=nullptr);

    InterestPtr make_subtopic(std::string prefix, std::string topicname,
            SubInfoPtr subinfo=nullptr);

    InterestPtr make_submani(std::string prefix, std::string scv_name, std::string dataname,
            SubInfoPtr subinfo=nullptr);

    InterestPtr make_subdata(std::string prefix, std::string dataname, long sequence);

    InterestPtr make_sublocal(std::string prefix, std::string topicname,
            SubInfoPtr subinfo=nullptr);
};

#endif /* __PSKCMD_HPP_ */
