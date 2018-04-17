import enum
import hashlib


class MessageType(enum.Enum):
    INPUT  = b'\x01'
    COMMIT = b'\x02'
    OUTPUT = b'\x03'
    PROOF  = b'\x04'


class HashChecker(object):
    def __init__(self, hash_algo):
        super().__init__()
        self.expected_hash_size = getattr(hashlib, hash_algo)().digest_size

    def check(self, hash_digest):
        if len(hash_digest) != self.expected_hash_size:
            raise ValueError('{} - not a valid hash'.format(hash_digest))

