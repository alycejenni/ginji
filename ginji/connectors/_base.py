from abc import ABC, abstractmethod

from ginji.config import config


class BaseConnector(ABC):
    """Connects to external services, e.g. uploads media or posts JSON notifications."""

    config_name = 'base'
    connector_type = 'base'

    def __init__(self):
        self._config = self.load_config()

    def load_config(self):
        return config.connector_config.get(self.config_name, {})

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    # def ifttt(self):
    #     config = self.config['ifttt']
    #     requests.post(config['url'], self.values)
    #     logger.debug('notified via ifttt')
    #
    # def instapush(self):
    #     config = self.config['instapush']
    #     app = instapush.App(config['id'], config['secret'])
    #     app.notify(config['event'], self.values)
    #     logger.debug('notified via instapush')


class BaseUploader(BaseConnector, ABC):
    config_name = 'uploader'
    connector_type = 'uploader'


class BaseNotifier(BaseConnector, ABC):
    config_name = 'notifier'
    connector_type = 'notifier'

    @abstractmethod
    def run(self, uploads=None, *args, **kwargs):
        pass
