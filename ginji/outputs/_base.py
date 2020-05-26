from abc import ABC, abstractmethod


class BaseOutput(ABC):
    """An object causing an effect in the system, e.g. a buzzer or a camera."""

    def __init__(self):
        self._uploaders = []
        self._notifiers = []

    def register_connectors(self, *connectors):
        """Register connectors to run after the fire event.

        :param connectors: Connector instances with a compatible .run() handler

        """
        for c in connectors:
            if not hasattr(c, 'connector_type'):
                continue
            elif c.connector_type == 'notifier':
                self._notifiers.append(c)
            elif c.connector_type == 'uploader':
                self._uploaders.append(c)

    @abstractmethod
    def fire(self, **kwargs):
        """Perform the output action."""
        pass

    @abstractmethod
    def connect(self, **kwargs):
        """Run the connector actions."""
        pass
