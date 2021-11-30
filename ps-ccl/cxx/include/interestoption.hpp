/*
 * interestoption.hpp
 *
 * parameters for interest packet
 */

#ifndef __INTERESTOPTION_HPP__
#define __INTERESTOPTION_HPP__


//#include <ndn-cxx/interest.hpp>

#include "psdcn.hpp"

using namespace ndn;

class InterestOption {
public:
    InterestOption()
    : m_canBePrefix(false)
    , m_mustBeFresh(true)
    , m_lifetime(10000)  // must be higher value than 4000
    {
    };

    bool m_canBePrefix;
    bool m_mustBeFresh;
    int64_t m_lifetime;
    optional<uint32_t> m_nonce;
    optional<uint8_t> m_hopLimit;
};

#endif /* __INTERESTOPTION_HPP__ */
