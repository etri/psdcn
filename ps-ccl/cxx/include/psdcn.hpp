/*
 * psdcn.hpp
 *
 * psdcn variables
 */

#ifndef __PSDCN_HPP__
#define __PSDCN_HPP__

#include <ndn-cxx/interest.hpp>
#include <ndn-cxx/face.hpp>

namespace ndn { namespace ptr_lib = boost; }

#include <rapidjson/document.h>
#include <rapidjson/writer.h>
#include <rapidjson/stringbuffer.h>

using namespace ndn;

using FacePtr = std::shared_ptr<Face>;
using InterestPtr = std::shared_ptr<Interest>;

using DocumentPtr = std::shared_ptr<rapidjson::Document>;

#endif /* __PSDCN_HPP__ */
