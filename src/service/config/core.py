from src.schemas.conf_model import Config
from src.service.utils.event_loop import init_new_loop

_config: Config = None


def init_conf():
    global _config

    _config = Config(
        global_event_loop=init_new_loop()
    )


def set_config(conf: Config):
    global _config
    _config = conf


def get_config():
    global _config

    if _config is None:
        raise RuntimeError("Config не заполнен")

    return _config