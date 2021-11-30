# encoding: cp949

"""
Logger for PSDCNv3.

Logger configuration is also described in PSDCNv3 configuration file.
"""

from psdcnv3.utils.config import config_value
import sys
import logging
import logging.handlers

__Logger_inited = None
logger = None

def init_logger(name="psdcnv3"):
    """
    Initialize a logger as specified in the configuration file.
    Currently, logging level, external file name for fileHandler, and
    stream for StreamHandler can be specified.
    """
    global __Logger_inited, logger

    if __Logger_inited:
        return logger

    logger = logging.getLogger(name)
    logger.propagate = False

    level = config_value('logger', 'level')
    logger.setLevel(eval('logging.' + level.upper()) if level else logging.WARNING)

    formatter = logging.Formatter(
        fmt='[{asctime}] {levelname}: {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{')

    file_max_bytes = 10 * 1024 * 1024
    fileHandler = logging.handlers.RotatingFileHandler(
        filename=config_value('logger', 'handlers', 'fileHandler'),
        maxBytes=file_max_bytes,
        backupCount=10)

    handlers = [fileHandler]
    streamName = config_value('logger', 'handlers', 'StreamHandler')
    if streamName is not None:
        handlers.append(logging.StreamHandler(stream=eval(streamName)))

    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    __Logger_inited = True
    return logger
