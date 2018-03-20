from sloth import Sloth
from . import BaseComputation


class SlothComputation(BaseComputation):

    def __init__(self, input_data=None, sloth_bits=2048, sloth_iterations=10000):
        super().__init__(input_data)
        self.input_data = input_data
        self.sloth_bits = sloth_bits
        self.sloth_iterations = sloth_iterations


    def compute(self):
        self._sloth = Sloth(
            data=self.input_data,
            bits=self.sloth_bits,
            iterations=self.sloth_iterations
        )
        self._sloth.compute()
        self._sloth.wait()
        self.output = self._sloth.final_hash
        self.output_proof = self._sloth.witness

