/*
 * logging.hpp
 *
 * logging module
 */

#ifndef __LOGGING_HPP__
#define __LOGGING_HPP__


#include <string>
#include <ndn-cxx/util/logger.hpp>

#define NDN_LOG_TRACE_SS( x ) \
do { \
    std::stringstream ss; \
    ss << x; \
    NDN_LOG_TRACE(ss.str()); \
} while (false)

#define NDN_LOG_DEBUG_SS( x ) \
do { \
    std::stringstream ss; \
    ss << x; \
    NDN_LOG_DEBUG(ss.str()); \
} while (false)

#define NDN_LOG_INFO_SS( x ) \
do { \
    std::stringstream ss; \
    ss << x; \
    NDN_LOG_INFO(ss.str()); \
} while (false)

#define NDN_LOG_WARN_SS( x ) \
do { \
    std::stringstream ss; \
    ss << x; \
    NDN_LOG_WARN(ss.str()); \
} while (false)

#define NDN_LOG_ERROR_SS( x ) \
do { \
    std::stringstream ss; \
    ss << x; \
    NDN_LOG_ERROR(ss.str()); \
} while (false)

#define NDN_LOG_FATAL_SS( x ) \
do { \
    std::stringstream ss; \
    ss << x; \
    NDN_LOG_FATAL(ss.str()); \
} while (false)


class LogSetting {
public:
    std::string target;
    std::string file_name;
    std::string format;
    std::string format_date_time;
    long file_ordering_window_sec;
    long max_size;
    long rotation_size;
};

void add_text_file_sink(LogSetting & setting);

void add_text_file_sink(std::string prefix, std::string target);

void remove_all_sinks();

#endif /* __LOGGING_HPP__ */
