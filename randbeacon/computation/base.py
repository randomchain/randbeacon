from abc import ABC, abstractmethod


class BaseComputation(ABC):
    def __init__(self, input_data=None):
        self.input_data = input_data
        self.output = None
        self.output_proof = None

    @abstractmethod
    def compute(self):
        pass
