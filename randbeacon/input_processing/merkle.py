from hashlib import sha256 as sha
from itertools import zip_longest
from merkletools import MerkleTools

class MerkleNode(object):

    """Docstring for MerkleNode. """

    def __init__(self, l_child=None, r_child=None, value=None, telemetry_data=None):
        self.l_child = l_child
        self.r_child = r_child
        self._value = value
        self.telemetry_data = telemetry_data

    @property
    def value(self):
        if self._value is None:
            self._value = sha(self.l_child.value + self.r_child.value).digest()
        return self._value

    def __repr__(self):
        return "Value {}".format(self.value.hex())

class MerkleTreeInputProcessor(object):

    """Docstring for MerkleTreeProcessor. """

    def __init__(self, input_data = None):
        self.input_data = input_data
        self.processed_data = None
        self.commitment = None
        self.catalog = {}
        self.mt = MerkleTools(hash_type="sha256")

    def process(self):
        self.mt.reset_tree()
        assert self.input_data is not None, "Input data must be provided before processing"
        assert self.input_data, "Input data must be provided before processing"
        self.mt.add_leaf(self.input_data, True)
        self.mt.make_tree()
        #self.processed_data = self.mt.get_merkle_root()
        self.processed_data = self.mt.levels[0][0]
        self.commitment = self.mt

        return self.processed_data

    def commit(self):
        if self.commitment is None:
            self.process()
        return self.commitment

if __name__ == "__main__":
    inp = [b'meme', b'pepe', b'trump']

    m = MerkleTreeInputProcessor(input_data=inp)

    m.process()

    print("PROCESSED DATA (Merkle root)")
    print(m.processed_data.hex())
