from merkletools import MerkleTools
import zmq
from zmq import Context, Poller
from logbook import Logger, StreamHandler
import sys

StreamHandler(sys.stdout).push_application()
log = Logger('Merkle')

ctx = Context.instance()

pull = ctx.socket(zmq.PULL)
pull.bind('tcp://*:12345')

push = ctx.socket(zmq.PUSH)
push.connect('tcp://localhost:11234')

sub = ctx.socket(zmq.SUB)
sub.connect('tcp://localhost:23456')
sub.setsockopt(zmq.SUBSCRIBE, b'process')


poller = Poller()
poller.register(pull, zmq.POLLIN)
poller.register(sub, zmq.POLLIN)

catalog = {}
mt = MerkleTools(hash_type="sha256")

def process():
    if not mt.leaves:
        raise AttributeError("Merkle tree has no leaves")
    mt.make_tree()

def start_poll():
    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            return

        if sub in socks:
            log.info('SUB {}'.format(sub.recv_multipart()))
            try:
                log.info('Make Tree')
                process()
                log.info('Merkle root {}'.format(mt.merkle_root.hex()))
                push.send(mt.merkle_root)
                mt.reset_tree()
            except Exception as e:
                log.error("Unable to create merkle tree -> {}".format(e))

        if pull in socks:
            inp = pull.recv()
            mt.add_leaf(inp, do_hash=True)
            log.info('{} : New leaf -> {}...'.format(len(mt.leaves), inp[:20]))

start_poll()
