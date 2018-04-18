from collections import defaultdict
from functools import lru_cache
from pprint import pprint
from flask import Flask, redirect, render_template_string, jsonify, abort
import sh
import ujson as json
import msgpack
from merkletools import MerkleTools

app = Flask(__name__)

JSON_FILE = '../output.json'

def read_latest_data():
    data = defaultdict(dict)
    latest_output_seq_no = 0
    for line in sh.tail('-n', '6', JSON_FILE, _iter=True):
        line_data = json.loads(line)
        if line_data['type'] == "OUTPUT":
            latest_output_seq_no = line_data['seq_no']
        data[line_data['type']][line_data['seq_no']] = {
            'timestamp': line_data['timestamp'],
            'data': line_data['data'],
        }
    return latest_output_seq_no, data

@lru_cache()
def read_seq_no(seq_no):
    seq_data = dict()
    with open(JSON_FILE, 'r') as file:
        for line in file:
            data = json.loads(line)
            if data['seq_no'] == seq_no:
                seq_data[data['type']] = {
                    'timestamp': data['timestamp'],
                    'data': data['data'],
                }
    return seq_data


@app.route('/')
def latest_full():
    latest_output_seq_no, data = read_latest_data()
    app.logger.info('latest seq_no: {}', latest_output_seq_no)
    latest_data = {t: v[latest_output_seq_no] for t, v in data.items()}
    latest_data['seq_no'] = latest_output_seq_no
    return jsonify(latest_data)

@app.route('/commit')
def latest_commit():
    latest_output_seq_no, data = read_latest_data()
    if latest_output_seq_no + 1 not in data['COMMIT']:
        return redirect('/')
    return jsonify({
        'COMMIT': data['COMMIT'][latest_output_seq_no + 1],
        'seq_no': latest_output_seq_no + 1,
    })

@app.route('/merkle/<int:seq_no>')
def merkle(seq_no):
    data = read_seq_no(seq_no)
    if not data:
        return abort(404)
    commit = data['COMMIT']['data']
    # mt = MerkleTools(hash_type='sha512')
    # mt.levels = msgpack.unpackb(bytes.fromhex(commit))
    levels = msgpack.unpackb(bytes.fromhex(commit))
    for i, level in enumerate(levels):
        levels[i] = list(map(lambda v: v.hex(), level))
    return jsonify(levels)

@app.route('/<int:seq_no>')
def get_by_seq_no(seq_no):
    return jsonify(read_seq_no(seq_no))

# @app.route('/<str:output_hash>')
# def get_by_output_hash(output_hash):
#     pass

if __name__ == "__main__":
    app.run('0.0.0.0', 5050)
