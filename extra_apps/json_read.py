from collections import defaultdict
from functools import lru_cache
import ujson as json
import msgpack
from merkletools import MerkleTools
from os import path
import glob

JSON_FOLDER = '../output_json/'

@lru_cache()
def read_data(json_file_path, parse=False):
    if path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            seq = json.loads(file.read())
        if parse:
            d = msgpack.unpackb(bytes.fromhex(seq['COMMIT']['data']))
            seq['COMMIT']['data'] = {
                'root': d[b'root'].hex(),
                'leaves': list(map(lambda l: l.hex(), d[b'leaves'])),
                'hash_type': d[b'hash_type'].decode('ascii')
            }
            if 'PROOF' in seq:
                d = msgpack.unpackb(bytes.fromhex(seq['PROOF']['data']))
                seq['PROOF']['data'] = {
                    'witness': d[b'witness'].hex(),
                    'bits': d[b'bits'],
                    'iterations': d[b'iterations'],
                }
        return seq
    return None

def read_latest_data(n_seq=1):
    data = defaultdict(dict)
    json_files = glob.iglob(path.join(JSON_FOLDER, '*.json'))
    json_files = list(reversed(sorted(json_files, key=path.getctime)))

    if json_files:
        data = []
        for json_file in json_files[:n_seq]:
            data.append(read_data(json_file))
        return data

    return None

def read_seq_no(seq_no, parse=False):
    seq_data = dict()
    json_file_path = path.join(JSON_FOLDER, str(seq_no) + '.json')
    return read_data(json_file_path, parse)

@lru_cache()
def merkle(seq_no):
    data = read_seq_no(seq_no)
    if not data:
        raise Exception("No data")
    commit = data['COMMIT']['data']
    commit_dict = msgpack.unpackb(bytes.fromhex(commit))
    mt = MerkleTools(hash_type=commit_dict[b'hash_type'].decode('ascii'))
    mt.leaves = commit_dict[b'leaves']
    mt.make_tree()
    assert mt.merkle_root == commit_dict[b'root']
    return mt
