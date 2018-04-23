import datetime
import os
import sys
import enum
import json
import zmq
from zmq import Context
import click
from logbook import StreamHandler, Logger


StreamHandler(sys.stdout).push_application()
log = Logger('json')

DIR = None


class EntryType(enum.Enum):
    COMMIT = b'\x02'
    OUTPUT = b'\x03'
    PROOFS = b'\x04'


def update_file(seq_no, entry_type, data):
    timestamp = str(datetime.datetime.utcnow())
    try:
        data = data.decode('ascii')
        log.debug("data decoded as ascii")
    except:
        data = data.hex()
        log.debug("data decoded as hex")
    data_dict = {
        entry_type.name: {
            'timestamp': timestamp,
            'data': data,
        },
    }
    log.debug('new data -> seq no: {} | {}', seq_no, data_dict)
    if DIR:
        file_path = os.path.join(DIR, str(seq_no) + '.json')
        if os.path.exists(file_path):
            with open(file_path, mode='r') as fh:
                data_dict.update(json.loads(fh.read()))
                log.debug('merged with existing data: seq no {}', seq_no)
        with open(file_path, mode='w') as fh:
            fh.write(json.dumps(data_dict) + "\n")
            log.debug('json file written: seq no {}', seq_no)


def fetch_loop(sub):
    while True:
        data_list = sub.recv_multipart()
        if len(data_list) != 3:
            log.warn('Ignoring bad data -> {}', data_list)
            continue
        header, seq_no, data = data_list
        try:
            entry_type = EntryType(header)
            seq_no = int.from_bytes(seq_no, byteorder='big')
        except:
            log.warn('Ignoring bad message -> {} | {} | {}', header, seq_no, data)
            continue
        update_file(seq_no, entry_type, data)


@click.command()
@click.option('--sub-connect', default="tcp://localhost:44567")
@click.option('--json-output-dir', default=None)
def main(sub_connect, json_output_dir):
    global DIR
    DIR = json_output_dir

    if DIR is None:
        log.info('No output dir... dry run activated')
    else:
        if os.path.exists(DIR):
            log.info('Output dir: "{}" selected', DIR)
        else:
            os.makedirs(DIR)
            log.info('Output dir: "{}" created', DIR)

    ctx = Context()
    sub = ctx.socket(zmq.SUB)
    sub.connect(sub_connect)
    log.info("Sub connected to {}", sub_connect)
    sub.setsockopt(zmq.SUBSCRIBE, EntryType.COMMIT.value)
    sub.setsockopt(zmq.SUBSCRIBE, EntryType.OUTPUT.value)
    sub.setsockopt(zmq.SUBSCRIBE, EntryType.PROOFS.value)

    fetch_loop(sub)

if __name__ == "__main__":
    main(auto_envvar_prefix="JSON_PUBLISHER")
