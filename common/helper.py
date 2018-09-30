from pathlib import Path
import json
import logging
import re
import time


def load_config(name):
    config = 'config/{}'.format(name)
    local = 'config/local/`{}'.format(name)

    config_path = Path(config)
    if not config_path.is_file():
        raise FileNotFoundError

    with open(config) as fp:
        json_config = json.load(fp)

    local_path = Path(local)
    if local_path.is_file():
        with open(local) as fp:
            other_config = json.load(fp)

        for key, value in other_config.items():
            json_config[key] = value

    return json_config


def load_logger(name):
    try:
        log4p = load_config("log4p.cfg")
        if name in log4p:
            config = log4p[name]
            path = config['file']
            mode = config['mode']
            level = config['level']
            fmt = config['format']
            stream = config['stream']
        else:
            path = 'log/{}.log'.format(name)
            mode = 'a'
            level = 'INFO'
            fmt = '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
            stream = True
    except FileNotFoundError:
        path = 'log/{}.log'.format(name)
        mode = 'a'
        level = 'INFO'
        fmt = '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
        stream = True

    logger = logging.getLogger(name)
    formatter = logging.Formatter(fmt)
    file_handler = logging.FileHandler(path, mode=mode)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    if stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    logger.setLevel(level)
    return logger


def load_analyser(relative_path):
    with open('analysis/{}'.format(relative_path)) as fp:
        exec(fp.read())
        return locals()['d_analysis']


class Constants(object):
    call_logger = load_logger('CallStalker')


def callstalker(func):
    def wrapper(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
            Constants.call_logger.debug("{}{} -> {}".format(func.__name__, args, ret.__dict__ if ret else ret))
            return ret
        except Exception as ex:
            Constants.call_logger.error("{}{} -> {}".format(func.__name__, args, ex))
            raise ex

    return wrapper


def config2seconds(cfg):
    config = {
        'M': 30 * 24 * 60 * 60,
        'D': 24 * 60 * 60,
        'h': 60 * 60,
        'm': 60,
        's': 1
    }
    return int(re.search(r'\d+', cfg).group()) * config[cfg[-1]]


def dump(obj):
    dict_ = dict(obj.__dict__)

    for key, value in obj.__dict__.items():
        if '__dict__' in dir(value):
            dict_[key] = dump(value)
        elif isinstance(value, list):
            new_list = []
            for i in value:
                if '__dict__' in dir(i):
                    new_list.append(dump(i))
                else:
                    new_list.append(i)
            dict_[key] = new_list
    return {type(obj).__name__: dict_}


def dump_to_file(obj, file=None, extra=None):
    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            try:
                ret = json.JSONEncoder.default(self, obj)
                return ret
            except:
                return str(obj)

    if file is None:
        file = 'dump/{}_{}_dump.json'.format(int(time.time()), type(obj).__name__)

    with open(file, 'w') as fp:
        dict_ = dump(obj)
        dict_['extra'] = extra
        json.dump(dict_, fp=fp, indent=2, sort_keys=True, cls=SetEncoder)
