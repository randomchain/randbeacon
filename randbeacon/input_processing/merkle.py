from hashlib import sha256 as sha
from itertools import zip_longest

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

    def _build_merkle_tree(self):
        # prepare leaf nodes
        nodes = []
        for leaf_data in self.input_data:
            node = MerkleNode(
                value=sha(leaf_data).digest(),
                telemetry_data=leaf_data,
            )
            self.catalog[node.value] = node
            nodes.append(node)

        # Build tree, one level at a time
        while len(nodes) > 1:
            new_nodes = []
            for l, r in zip_longest(*[iter(nodes)] * 2, fillvalue=None):
                if r is None:
                    r = MerkleNode(
                        value=sha(b"").digest(),
                        telemetry_data=b"",
                    )
                node = MerkleNode(l, r)
                self.catalog[node.value] = node
                new_nodes.append(node)
            nodes = new_nodes

        return nodes[0]

    def process(self):
        assert self.input_data is not None, "Input data must be provided before processing"
        merkle_tree_root = self._build_merkle_tree()
        self.processed_data = merkle_tree_root.value
        self.commitment = merkle_tree_root

        return self.processed_data

    def commit(self):
        if self.commitment is None:
            self.process()
        return self.commitment

    @staticmethod
    def print_tree(node, indentation=0, verb=False):
        if verb:
            print("    " * indentation, node, node.telemetry_data if node.telemetry_data else "")
        else:
            print("    " * indentation, "---", node.telemetry_data[:10] if node.telemetry_data else "")

        if node.l_child is not None:
            MerkleTreeInputProcessor.print_tree(node.l_child, indentation + 1)
        if node.r_child is not None:
            MerkleTreeInputProcessor.print_tree(node.r_child, indentation + 1)


if __name__ == "__main__":
    inp = [b'meme', b'pepe', b'trump']

    m = MerkleTreeInputProcessor(input_data=inp)

    m.process()

    print("PROCESSED DATA (Merkle root)")
    print(m.processed_data.hex())

    print("COMMITMENT (Merkle tree)")
    MerkleTreeInputProcessor.print_tree(m.commitment)
