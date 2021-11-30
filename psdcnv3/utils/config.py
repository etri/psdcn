import yaml

__configLoaded: bool = False
__configuration = None

def load_config(path=None, force=False):
    """
    Load configuration data from the given `path`.
    If `path` is not given or is None, 'psdcnv3.config' is used instead.
    The content of the configuration file should be conformant to YAML format.

    :param path: The file path from which the configuration will be loaded.
    :param force: Load the configuration data even if it has already been loaded.
    :return: Configuration data parsed from `path` as a dict.
    """
    global __configuration, __configLoaded

    if __configLoaded and not force:
        return __configuration
    if not path:
        path = 'psdcnv3.config'
    try:
        with open(path, 'r') as file:       # encoding='cp949', 'utf-8', ...
            __configuration = yaml.safe_load(file)
    except FileNotFoundError:
        # raise FileNotFoundError(f"Configuration file not found at '{path}'")
        _configuration = {}
    __configLoaded = True
    return __configuration

def config_value(*keys: [str]):
    """
    Retrieve configuration valu for the given key sequence.
    If no keys are given, the whole configuration data is returned as a Dict.
    If keys are given, they are all applied in sequence, and return the final value.
    If any key of the keys cannot be applied, returns None instead.

    For example,
        config_value() returns all the confiuration values as a Dict.
        config_value('logger') returns the values(s) for the given key 'logger'.
            if key 'logger' is not defined, returns None instead.
        config_value('logger', 'handlers') returns the values(s) for the key 'handlers'
            which is under the key 'logger'.  If either key 'logger' or 'handlers'
            under 'logger' is not defined, returns None instead.

    :param *keys: list of component keys
    :type *keys: [str]
    """
    if not __configLoaded:
        load_config()
    value = __configuration
    try:
        for key in keys:
            if key in value:
                value = value[key]
            else:
                value = None
                break
    except:
        value = None
    return value

def config_default(name, default):
    value = config_value(name)
    return value if value else default

