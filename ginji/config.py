import json
import os
import logging


class Config(object):
    def __init__(self, path=None):
        config_dict = self._load(path)
        self.root = config_dict.get('root', os.path.dirname(os.path.realpath(__file__ + '/..')))
        self.file_prefix = config_dict.get('file_prefix', 'cat')
        self._log_level = config_dict.get('log_level', 'DEBUG').upper()
        self.input_config = config_dict.get('inputs', {})
        self.output_config = config_dict.get('outputs', {})
        self.connector_config = config_dict.get('connectors', {})

    def _load(self, path):
        if path is None:
            path = os.getenv('GINJI_CONFIG')
        if path is None:
            path = os.path.join(os.getcwd(), 'config.json')
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, 'r') as f:
                return json.load(f)
        else:
            return {}

    @property
    def log_level(self):
        return logging.getLevelName(self._log_level)

    @log_level.setter
    def log_level(self, level: str):
        self._log_level = level.upper()

    def dump(self):
        return {
            'root': self.root,
            'file_prefix': self.file_prefix,
            'inputs': self.input_config,
            'outputs': self.output_config,
            'connectors': self.connector_config,
            'log_level': self.log_level
            }


config = Config()

logger = logging.getLogger('ginji')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(config.log_level)
