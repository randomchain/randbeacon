import time
import sys
from collections import deque
import click
import msgpack
import zmq
from logbook import Logger, StreamHandler
from merkletools import MerkleTools
from zmq import Context, Poller
from ..utils import MessageType, Status, HashChecker


log = Logger('Merkle')
ctx = Context.instance()
mt = None
worker_deque = deque()


def process():
    if not mt.leaves:
        raise AttributeError("Merkle tree has no leaves")
    mt.make_tree()


def recv_input(pull, hash_checker):
    inp = pull.recv()
    log.debug('pull: recv -> {}'.format(inp.hex()))
    try:
        hash_checker.check(inp)
    except:
        log.warn('Bad hash received! -> {}', inp)
    else:
        mt.add_leaf(inp, do_hash=False)
        log.info('leaf added | leaves: {}'.format(len(mt.leaves)))


def recv_from_comp(router):
    compute_id, msg_type, status = router.recv_multipart()
    try:
        log.debug('router: recv -> id: {} | {} | {}',
                  compute_id, MessageType(msg_type), Status(status))
    except:
        log.debug('router: recv -> id: {} | {} | {}',
                  compute_id, msg_type, status)
    if msg_type != MessageType.STATUS:
        log.warn('Expected messagetype of {} got {}',
                 MessageType.STATUS, msg_type)
    elif status == Status.READY:
        router.send_multipart([compute_id, MessageType.STATUS, Status.OK])
        if compute_id not in worker_deque:
            worker_deque.append(compute_id)
            log.info('Worker "{}" added to deque ({})', compute_id, len(worker_deque))
    elif status == Status.OK:
        log.info('Worker "{}" received data', compute_id)
    elif status == Status.ERROR:
        log.warn('Worker "{}" reported error in data!', compute_id)


def send_to_comp(router, compute_id, seq_no):
    # Send condensed input data, i.e. Merkle root
    router.send_multipart([
        compute_id,
        MessageType.INPUT,
        seq_no.to_bytes(2, byteorder='big'),
        mt.merkle_root,
    ])
    log.debug('router: send to {} -> {} | {} | {}',
              compute_id, MessageType.INPUT, seq_no, mt.merkle_root.hex())
    # Send commitment data, i.e. leaves of Merkle tree
    data = msgpack.packb({'root': mt.merkle_root, 'leaves': mt.leaves, 'hash_type': mt._hash_type})
    router.send_multipart([
        compute_id,
        MessageType.COMMIT,
        seq_no.to_bytes(2, byteorder='big'),
        data,
    ])
    log.debug('router: send to {} -> {} | {} | {}...',
              compute_id, MessageType.COMMIT, seq_no, data.hex()[:20])


def start_poll(pull, router, hash_checker, gather_time):
    seq_no = 0
    last_process = time.time()
    poller = Poller()
    poller.register(pull, zmq.POLLIN)
    poller.register(router, zmq.POLLIN)
    while True:
        try:
            socks = dict(poller.poll(timeout=gather_time * 100))
        except KeyboardInterrupt:
            return

        if pull in socks:
            recv_input(pull, hash_checker)

        if router in socks:
            recv_from_comp(router)

        if worker_deque and time.time() - last_process >= gather_time:
            compute_id = worker_deque.popleft()
            last_process = time.time()
            try:
                log.info('Make Tree')
                process()
                log.info('Merkle root {}', mt.merkle_root.hex())

                send_to_comp(router, compute_id, seq_no)

                mt.reset_tree()
                log.info("Reset tree")

                if seq_no == 0xFFFF:
                    seq_no = 0
                else:
                    seq_no += 1
            except Exception as e:
                log.error("Unable to create merkle tree -> {}".format(e))
        else:
            log.debug('time since last {}, deque size {}',
                      time.time() - last_process, len(worker_deque))


@click.command()
@click.option('--hash-algo', default="sha512")
@click.option('--gather-time', default=5.0)
@click.option('--pull-addr', default="tcp://*:11234")
@click.option('--pull-type', type=click.Choice(['bind', 'connect']), default='bind')
@click.option('--router-addr', default="tcp://*:22345")
@click.option('--router-type', type=click.Choice(['bind', 'connect']), default='bind')
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(hash_algo, gather_time, pull_addr, pull_type, router_addr, router_type, verbose):
    global mt
    StreamHandler(sys.stdout, level='DEBUG' if verbose else 'INFO').push_application()
    mt = MerkleTools(hash_type=hash_algo)
    log.info('Tree using {} hashing algorithm', hash_algo)
    hash_checker = HashChecker(hash_algo)

    pull = ctx.socket(zmq.PULL)
    log.info('{} PULL socket to {}',
             'Binding' if pull_type == 'bind' else 'Connecting', pull_addr)
    getattr(pull, pull_type)(pull_addr)

    router = ctx.socket(zmq.ROUTER)
    log.info('{} ROUTER socket to {}',
             'Binding' if router_type == 'bind' else 'Connecting', router_addr)
    getattr(router, router_type)(router_addr)

    start_poll(pull, router, hash_checker, gather_time)

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_PROCESSOR_MERKLE")

