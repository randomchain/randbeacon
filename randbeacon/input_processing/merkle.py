from merkletools import MerkleTools
import zmq
from zmq import Context, Poller
import logbook
from logbook import Logger, StreamHandler
import sys
import click

StreamHandler(sys.stdout, level=logbook.INFO).push_application()
log = Logger('merkle')
sub_log = Logger('sub')
push_log = Logger('push')
pull_log = Logger('pull')

ctx = Context.instance()

HASH_LEAVES = None
mt = None

def process():
    if not mt.leaves:
        raise AttributeError("Merkle tree has no leaves")
    mt.make_tree()

def start_poll(pull, push, sub):
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
                push.send_multipart([b"root", mt.merkle_root])
                push_log.info('merkle_root pushed')
                # push.send_multipart([b"tree", mt.levels])
                # push_log.info('merkle_tree pushed')
                mt.reset_tree()
            except Exception as e:
                log.error("Unable to create merkle tree -> {}".format(e))

        if pull in socks:
            hashed, inp = pull.recv_multipart()
            pull_log.info('recv -> {} | {}...'.format(hashed, inp[:20]))
            pull_log.debug('{} | {}'.format(hashed, inp))
            hashed = (hashed == b'\x01')
            mt.add_leaf(inp, do_hash=not hashed)
            log.info('leaves: {}, added {} leaf'.format(len(mt.leaves), 'pre hashed' if hashed else 'and hashed'))

@click.command()
@click.option('--hash-algo', default="sha512")
@click.option('--hash-leaves/--not-hash-leaves', default=False)
@click.option('--pull-bind', default="tcp://*:12345")
@click.option('--push-connect', default="tcp://localhost:11234")
@click.option('--sub-connect', default="tcp://localhost:23456")
def main(hash_algo, hash_leaves, pull_bind, push_connect, sub_connect):
    global mt, HASH_LEAF
    mt = MerkleTools(hash_type=hash_algo)
    HASH_LEAVES = hash_leaves
    log.info('Hashing algo: {}, hash leaves: {}'.format(hash_algo, hash_leaves))

    pull_log.info('Binding PULL socket to {}'.format(pull_bind))
    pull = ctx.socket(zmq.PULL)
    pull.bind(pull_bind)

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
