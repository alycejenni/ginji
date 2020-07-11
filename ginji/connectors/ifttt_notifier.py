import requests

from ._base import BaseNotifier
from ginji.config import logger


class IFTTTNotifier(BaseNotifier):
    config_name = 'ifttt'

    def load_config(self):
        basic_config = super(IFTTTNotifier, self).load_config()
        return {
            'url': basic_config.get('url', 'invalid-url')
            }

    def run(self, uploads=None, value2='', value3=''):
        payload = {
            'value1': uploads.get('s3', ''),
            'value2': value2,
            'value3': value3
            }

        requests.post(self._config['url'], payload)
        logger.debug('Sent payload to IFTTT notifier.')
