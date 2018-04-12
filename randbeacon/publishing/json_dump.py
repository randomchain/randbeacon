import datetime
import sys
import enum
import zmq
from zmq import Context
import click
import json
from logbook import StreamHandler, Logger

StreamHandler(sys.stdout).push_application()
log = Logger('json')

FILE = None

class EntryType(enum.Enum):
    COMMIT = b'\x02'
    OUTPUT = b'\x03'
    PROOFS = b'\x04'

def update_file(entry_type, seq_no, data):
    t = str(datetime.datetime.utcnow())
    try:
        data = data.decode('ascii')
    except:
        data = data.hex()
    line = json.dumps({
        'timestamp': t,
        'type': entry_type,
        'seq_no': seq_no,
        'data': data,
    })
    if FILE == '-':
        fh = sys.stdout
    else:
        fh = open(FILE, "a+")
    fh.write(line + "\n")
    if FILE != '-':
        fh.close()

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
            log.warn('Unable to interpret message... ignoring')
            continue
        update_file(entry_type.name, seq_no, data)

@click.command()
@click.option('--sub-connect', default="tcp://localhost:6666")
@click.option('--json-output', default='-')
def main(sub_connect, json_output):
    global FILE
    FILE = json_output

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
