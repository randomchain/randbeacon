import enum
import sys
from functools import reduce
import hashlib
from hashlib import sha512
from operator import concat

import click
import logbook
import msgpack
import zmq
from logbook import Logger, StreamHandler
from zmq import Context, Poller

class MessageType(enum.Enum):
    INPUT = b'\x01'
    COMMIT = b'\x02'

StreamHandler(sys.stdout, level=logbook.DEBUG).push_application()
log = Logger('Concat')

ctx = Context.instance()

INPUT_DATA = []
HASHER = None

def process():
    if len(INPUT_DATA) == 0:
        raise AttributeError("Input has no elements to concat")
    processed_data = reduce(concat, INPUT_DATA)
    return processed_data

def start_poll(pull, push, sub):
    global INPUT_DATA
    seq_no = 0
    poller = Poller()
    poller.register(pull, zmq.POLLIN)
    poller.register(sub, zmq.POLLIN)
    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            return

        if sub in socks:
            log.debug('recv -> {}'.format(sub.recv_multipart()))
            try:
                log.info('Concatting...')
                concat_string = process()
                concat_string_hash = HASHER(concat_string).digest()

                # Send final hash
                push.send_multipart([
                    MessageType.INPUT.value,
                    seq_no.to_bytes(2, byteorder='big'),
                    concat_string_hash,
                ])
                log.debug('send -> {} | {} | {}', MessageType.INPUT.name, seq_no, concat_string_hash.hex())

                # Send original concatted string
                push.send_multipart([
                    MessageType.COMMIT.value,
                    seq_no.to_bytes(2, byteorder='big'),
                    concat_string,
                ])
                log.debug('send -> {} | {} | {}...', MessageType.COMMIT.name, seq_no, concat_string[:20])

                INPUT_DATA.clear()
                log.info("Reset concat")

                if seq_no == 0xFFFF:
                    seq_no = 0
                else:
                    seq_no += 1
            except Exception as e:
                log.error("Could not concat inputs -> {}".format(e))

        if pull in socks:
            inp = pull.recv()
            log.debug('recv -> {}'.format(inp.hex()))
            INPUT_DATA.append(inp)
            log.info('Input added | Elements: {}'.format(len(INPUT_DATA)))

@click.command()
@click.option('--hash-algo', default="sha512")
@click.option('--pull-addr', default="tcp://*:11234")
@click.option('--pull-type', type=click.Choice(['bind', 'connect']), default='bind')
@click.option('--push-connect', default="tcp://localhost:22345")
@click.option('--sub-connect', default="tcp://localhost:33456")
def main(hash_algo, pull_addr, pull_type, push_connect, sub_connect):
    global HASHER
    log.info('Concat using {} hashing algorithm'.format(hash_algo))

    HASHER = getattr(hashlib, hash_algo)

    pull = ctx.socket(zmq.PULL)
    log.info('{} PULL socket to {}'.format('Binding' if pull_type == 'bind' else 'Connecting', pull_addr))
    getattr(pull, pull_type)(pull_addr)

    log.info('Connecting PUSH socket to {}'.format(push_connect))
    push = ctx.socket(zmq.PUSH)
    push.connect(push_connect)

    log.info('Connecting SUB socket to {}'.format(sub_connect))
    sub = ctx.socket(zmq.SUB)
    sub.connect(sub_connect)
    sub.setsockopt(zmq.SUBSCRIBE, b'process')

    start_poll(pull, push, sub)

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_PROCESSOR_CONCAT")
