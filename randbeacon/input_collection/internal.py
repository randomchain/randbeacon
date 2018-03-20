from . import BaseInputCollector
from os import urandom


class UrandomInputCollector(BaseInputCollector):
    RANDOM_BYTES = 1024

    def collect(self, duration=None):
        self.inputs = [urandom(self.RANDOM_BYTES)]

    @property
    def collected_inputs(self):
        return iter(self.inputs)
