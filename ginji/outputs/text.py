from ._base import BaseOutput


class TextOutput(BaseOutput):
    def fire(self, value):
        print(value)
