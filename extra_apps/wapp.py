from collections import defaultdict
from pprint import pprint
from flask import Flask, redirect, render_template_string, jsonify
import sh
import ujson as json

app = Flask(__name__)

JSON_FILE = '../output.json'
LINES_PER_SEQ = 3

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

def read_seq_no(seq_no):
    with open(JSON_FILE, 'r') as file:
        first_line = json.loads(file.readline())
        found_seq_no = first_line['seq_no']
        target_line = (seq_no - found_seq_no) * 3
        file.seek(target_line - 1, 0)
        print(file.readline())


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
    pass

@app.route('/<int:seq_no>')
def get_by_seq_no(seq_no):
    read_seq_no(seq_no)

# @app.route('/<str:output_hash>')
# def get_by_output_hash(output_hash):
#     pass

if __name__ == "__main__":
    app.run('0.0.0.0', 5050)

