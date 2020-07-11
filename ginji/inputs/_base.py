import threading
from abc import ABC, abstractmethod
from ginji.config import config


class BaseInput(ABC):
    """An object providing data to the system, e.g. a switch or a light sensor."""
    config_name = 'base'

    def __init__(self):
        self._outputs = []
        self.cont = True
        self.thread = threading.Thread(target=self.run)
        self._config = self.load_config()
        self.setup()

    def load_config(self):
        return config.input_config.get(self.config_name, {})

    def register_outputs(self, *outputs):
        """Register output instances to be fired when the input changes.

        :param outputs: An Output instance with a compatible .fire() handler.

        """
        self._outputs += outputs

    def output(self, *args, **kwargs):
        for o in self._outputs:
            o.fire(*args, **kwargs)

    def start(self):
        self.cont = True
        if not self.thread.is_alive():
            self.thread.start()

    def stop(self):
        self.cont = False
        self.thread.join()

    @abstractmethod
    def setup(self):
        """Used to set up the input (or reset it to its initial state)."""
        pass

    @property
    @abstractmethod
    def value(self):
        """The current value of the input.

        :returns: An object representing the input's current state, e.g. a boolean
            for an on/off input.

        """
        return None

    @abstractmethod
    def run(self):
        pass
