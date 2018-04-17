import enum
import sys
import click
import logbook
import msgpack
import zmq
from logbook import Logger, StreamHandler
from merkletools import MerkleTools
from zmq import Context, Poller
from ..utils import MessageType, HashChecker


log = Logger('Merkle')
ctx = Context.instance()
mt = None


def process():
    if not mt.leaves:
        raise AttributeError("Merkle tree has no leaves")
    mt.make_tree()


def start_poll(pull, push, sub, hash_checker):
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
            log.debug('sub: recv -> {}'.format(sub.recv_multipart()))
            try:
                log.info('Make Tree')
                process()
                log.info('Merkle root {}'.format(mt.merkle_root.hex()))
                push.send_multipart([
                    MessageType.INPUT.value,
                    seq_no.to_bytes(2, byteorder='big'),
                    mt.merkle_root,
                ])
                log.debug('push: send -> {} | {} | {}', MessageType.INPUT.name, seq_no, mt.merkle_root.hex())

                data = msgpack.packb(mt.levels)
                push.send_multipart([
                    MessageType.COMMIT.value,
                    seq_no.to_bytes(2, byteorder='big'),
                    data,
                ])
                log.debug('push: send -> {} | {} | {}...', MessageType.COMMIT.name, seq_no, data.hex())

                mt.reset_tree()
                log.info("Reset tree")

                if seq_no == 0xFFFF:
                    seq_no = 0
                else:
                    seq_no += 1
            except Exception as e:
                log.error("Unable to create merkle tree -> {}".format(e))

        if pull in socks:
            inp = pull.recv()
            log.debug('pull: recv -> {}'.format(inp.hex()))
            try:
                hash_checker.check(inp)
            except:
                log.warn('Bad hash received! -> {}', inp)
                continue
            mt.add_leaf(inp, do_hash=False)
            log.info('leaf added | leaves: {}'.format(len(mt.leaves)))


@click.command()
@click.option('--hash-algo', default="sha512")
@click.option('--pull-addr', default="tcp://*:11234")
@click.option('--pull-type', type=click.Choice(['bind', 'connect']), default='bind')
@click.option('--push-connect', default="tcp://localhost:22345")
@click.option('--sub-connect', default="tcp://localhost:33456")
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(hash_algo, pull_addr, pull_type, push_connect, sub_connect, verbose):
    global mt
    StreamHandler(sys.stdout, level='DEBUG' if verbose else 'INFO').push_application()
    mt = MerkleTools(hash_type=hash_algo)
    log.info('Tree using {} hashing algorithm'.format(hash_algo))
    hash_checker = HashChecker(hash_algo)

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

    start_poll(pull, push, sub, hash_checker)

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_PROCESSOR_MERKLE")
