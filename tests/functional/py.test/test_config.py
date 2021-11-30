"""
Config-related tests
"""

import sys
sys.path.append("../../..")

from psdcnv3.utils import load_config, config_value
import os.path

CONFIG_FILE = "test.config"
_CONFIG_FILE_EXISTS = os.path.isfile(CONFIG_FILE)

def test_load_config():
    result = load_config(CONFIG_FILE)
    if _CONFIG_FILE_EXISTS:
        assert result
    else:
        assert not result

def test_0ary():
    if _CONFIG_FILE_EXISTS:
        assert config_value() is not None
    else:
        assert True

def test_unary():
    if _CONFIG_FILE_EXISTS:
        assert config_value("network_prefix") == "/rn"
    else:
        assert True

def test_binary():
    if _CONFIG_FILE_EXISTS:
        assert config_value("logger", "level") is not None
    else:
        assert True

def test_binary_unknown():
    if _CONFIG_FILE_EXISTS:
        assert config_value("logger", "compressor") is None
    else:
        assert True

def test_ternary():
    if _CONFIG_FILE_EXISTS:
        assert config_value("logger", "handlers", "fileHandler") is not None
    else:
        assert True
