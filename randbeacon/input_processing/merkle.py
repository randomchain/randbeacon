from merkletools import MerkleTools
import msgpack
import zmq
from zmq import Context, Poller
import logbook
from logbook import Logger, StreamHandler
import sys
import click

INPUT_MSG_HEADER = b'\x01'
COMMITMENT_MSH_HEADER = b'\x02'

StreamHandler(sys.stdout, level=logbook.INFO).push_application()
log = Logger('merkle')
sub_log = Logger('sub')
push_log = Logger('push')
pull_log = Logger('pull')

ctx = Context.instance()

mt = None

def process():
    if not mt.leaves:
        raise AttributeError("Merkle tree has no leaves")
    mt.make_tree()

def start_poll(pull, push, sub):
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
            sub_log.info('recv -> {}'.format(sub.recv_multipart()))
            try:
                log.info('Make Tree')
                process()
                log.info('Merkle root {}'.format(mt.merkle_root.hex()))
                push.send_multipart([
                    INPUT_MSG_HEADER,
                    seq_no.to_bytes(2, byteorder='big'),
                    mt.merkle_root,
                ])
                push_log.info('merkle_root pushed')
                push.send_multipart([
                    COMMITMENT_MSH_HEADER,
                    seq_no.to_bytes(2, byteorder='big'),
                    msgpack.packb(mt.levels),
                ])
                push_log.info('merkle_tree pushed')
                mt.reset_tree()
                if seq_no == 0xFFFF:
                    seq_no = 0
                else:
                    seq_no += 1
            except Exception as e:
                log.error("Unable to create merkle tree -> {}".format(e))

        if pull in socks:
            inp = pull.recv()
            pull_log.info('recv -> {}'.format(inp.hex()))
            mt.add_leaf(inp, do_hash=False)
            log.info('leaf added | leaves: {}'.format(len(mt.leaves)))

@click.command()
@click.option('--hash-algo', default="sha512")
@click.option('--pull-addr', default="tcp://*:11234")
@click.option('--pull-type', type=click.Choice(['bind', 'connect']), default='bind')
@click.option('--push-connect', default="tcp://localhost:22345")
@click.option('--sub-connect', default="tcp://localhost:33456")
def main(hash_algo, pull_addr, pull_type, push_connect, sub_connect):
    global mt
    mt = MerkleTools(hash_type=hash_algo)
    log.info('Tree using {} hashing algorithm'.format(hash_algo))

    pull = ctx.socket(zmq.PULL)
    pull_log.info('{} PULL socket to {}'.format('Binding' if pull_type == 'bind' else 'Connecting', pull_addr))
    getattr(pull, pull_type)(pull_addr)

    push_log.info('Connecting PUSH socket to {}'.format(push_connect))
    push = ctx.socket(zmq.PUSH)
    push.connect(push_connect)

    sub_log.info('Connecting SUB socket to {}'.format(sub_connect))
    sub = ctx.socket(zmq.SUB)
    sub.connect(sub_connect)
    sub.setsockopt(zmq.SUBSCRIBE, b'process')

    start_poll(pull, push, sub)

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_PROCESSOR_MERKLE")
