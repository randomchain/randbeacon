from merkletools import MerkleTools

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
        assert self.input_data, "Input data cannot be empty"
        self.mt.add_leaves(self.input_data, do_hash=True)
        self.mt.make_tree()
        self.processed_data = self.mt.merkle_root
        self.commitment = self.mt.levels[:]

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
