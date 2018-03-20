from hashlib import sha512
from operator import concat
from functools import reduce

class ConcatSHA512InputProcessor(object):
    def __init__(self, input_data):
        super().__init__()
        self.input_data = input_data

    def process(self):
        self.processed_data = reduce(concat, self.input_data)
        return self.processed_data

    def commit(self):
        sha = sha512()
        sha.update(self.processed_data)
        self.commitment = self.processed_data, sha.hexdigest()
        return self.commitment
