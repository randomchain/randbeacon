from collections import defaultdict
from functools import lru_cache
from pprint import pprint
from flask import Flask, redirect, request, render_template, flash, jsonify, abort
import ujson as json
import msgpack
from merkletools import MerkleTools
from os import path
import glob
import requests

app = Flask(__name__, static_url_path='')
app.secret_key = 'randbeacon4life'

JSON_FOLDER = '../output_json/'


# @lru_cache()
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
        return abort(404)
    commit = data['COMMIT']['data']
    commit_dict = msgpack.unpackb(bytes.fromhex(commit))
    mt = MerkleTools(hash_type=commit_dict[b'hash_type'].decode('ascii'))
    mt.leaves = commit_dict[b'leaves']
    mt.make_tree()
    assert mt.merkle_root == commit_dict[b'root']
    return mt

@app.route('/listmerkle/<int:seq_no>')
def list_merkle(seq_no):
    mt = merkle(seq_no)
    levels = []
    for level in mt.levels:
        levels.append(list(map(lambda v: v.hex(), level)))
    return jsonify(levels)

@app.route('/merkle/<int:seq_no>.json')
def js_merkle(seq_no):
    mt = merkle(seq_no)
    merkle_tree = {
        "chart": {
            "container": "#OrganiseChart-simple"
        }
    }

    root = {
        'text': {'name': mt.merkle_root.hex()[:5]},
        'level': 0,
        'idx': 0,
        'children': []
    }

    num_levels = len(mt.levels)

    def find_children(node):
        if num_levels -1 == node['level']:
            return []
        else:
            next_level = node['level'] +1
            l_idx, r_idx = (node['idx'] * 2, node['idx'] * 2 + 1)
            try:
                l = mt.levels[next_level][l_idx]
                r = mt.levels[next_level][r_idx]
            except:
                return []
            l_child = {
                'text': {'name': l.hex()[:5]},
                'level': next_level,
                'idx': l_idx,
                'children': None
            }
            l_child['children'] = find_children(l_child)
            r_child = {
                'text': {'name': r.hex()[:5]},
                'level': next_level,
                'idx': r_idx,
                'children': None
            }
            r_child['children'] = find_children(r_child)
            return [l_child, r_child]

    root['children'] = find_children(root)

    merkle_tree['nodeStructure'] = root

    return jsonify(merkle_tree)

@app.route('/seq/<int:seq_no>')
def get_by_seq_no(seq_no):
    return render_template('seq.html', seq=read_seq_no(seq_no, parse=True))

@app.route('/input',methods = ['POST', 'GET'])
def input():
    inp_hash = None
    if request.method == 'POST':
        form_data = request.form
        beacon_req = requests.post('http://localhost:8080', json={'utf-8': form_data['input']})
        inp_hash = beacon_req.json()['hash']
        flash('Input supplied with hash: {}'.format(inp_hash), 'success')
    return render_template('input.html', input_hash=inp_hash)

@app.route('/commit/<int:seq_no>')
def commit(seq_no):
    mt = merkle(seq_no)
    return render_template('commit.html', seq_no=seq_no, leaves=map(lambda l: l.hex(), mt.leaves))

@app.route('/')
def home():
    latest_n = read_latest_data(20)
    return render_template('index.html', outputs=latest_n)


if __name__ == "__main__":
    app.run('0.0.0.0', 5050)
