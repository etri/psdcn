/*
 * logging.cpp
 *
 * loggin module
 */

#include "logging.hpp"

#include <string>

#include <ndn-cxx/util/logger.hpp>

#include <boost/log/common.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>
#include <boost/log/sinks/text_ostream_backend.hpp>
#include <boost/core/null_deleter.hpp>
#include <boost/log/sinks.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/expressions/attr.hpp>
#include <boost/log/expressions/formatters/date_time.hpp>

#include <boost/log/utility/record_ordering.hpp>
#include <boost/log/support/date_time.hpp>


namespace logging = boost::log;
namespace attrs = boost::log::attributes;
namespace src = boost::log::sources;
namespace sinks = boost::log::sinks;
namespace expr = boost::log::expressions;
namespace keywords = boost::log::keywords;

using namespace ndn::util;

BOOST_LOG_ATTRIBUTE_KEYWORD(timestamp, "Timestamp", std::string)

void add_text_file_sink(std::string prefix, std::string target)
{
    LogSetting logSetting;
    //logSetting.file_name = "subscriber-%Y%m%d_%H:%M.txt";
    logSetting.file_name = prefix+"-%Y%m%d_%H%M-%3N.txt";
    logSetting.format = "[%TimeStamp%] (%Severity%) : %Message%";
    logSetting.format_date_time = "%Y-%m-%d %H:%M:%S.%f";
    logSetting.file_ordering_window_sec = 1;
    logSetting.rotation_size = 10*1024*1024;
    logSetting.max_size = 100*1024*1024;
    logSetting.target = target;

    logging::core::get()->remove_all_sinks();

    std::string filename, format;
    long rotation_size = 16384;

    if(logSetting.file_name.empty()) {
        filename = "log_%Y%m%dT%H%M%S-%N.txt";
    } else {
        filename = logSetting.file_name;
    }
    if(logSetting.format.empty()) {
        format = "[%TimeStamp%] (%Severity%) : %Message%";
    } else {
        format = logSetting.format;
    }
    if(0 < logSetting.rotation_size) {
        rotation_size = logSetting.rotation_size;
    }

    boost::shared_ptr< sinks::text_file_backend > file_backend = boost::make_shared< sinks::text_file_backend >(
        keywords::file_name = filename,
        keywords::rotation_size = rotation_size,
        keywords::auto_flush = true,
        keywords::open_mode = (std::ios::out | std::ios::app | std::ios::ate),

        // ratate file : day
        keywords::time_based_rotation = sinks::file::rotation_at_time_point(0, 0, 0),

        // 1 minute
        //keywords::time_based_rotation = sinks::file::rotation_at_time_interval(boost::posix_time::minutes(1)),

        keywords::format = format,
        keywords::min_free_space= logSetting.max_size * 10
    );

    file_backend->auto_flush(true);

    typedef sinks::synchronous_sink< sinks::text_file_backend > sink_t;
    boost::shared_ptr< sink_t > sink(new sink_t(file_backend));

    namespace expr = boost::log::expressions;
    sink->set_formatter(
            expr::stream << expr::attr<std::string>(timestamp.get_name()) << " "
                    << std::setw(5)
                    << expr::attr<LogLevel>(log::severity.get_name()) << ": "
                    << "[" << expr::attr<std::string>(log::module.get_name())
                    << "] " << expr::smessage);

    sink->locked_backend()->set_file_collector(
            sinks::file::make_collector(keywords::target = logSetting.target,
                    keywords::max_size = logSetting.max_size));

    sink->locked_backend()->scan_for_files();

    logging::core::get()->add_sink(sink);
}
