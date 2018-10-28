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


log = Logger('inp. processor')

class BaseInputProcessor(object):

    def __init__(self, pull_addr, pull_type, router_addr, router_type, gather_time, hash_algo):
        self.ctx = Context.instance()
        self.worker_deque = deque()
        self.gather_time = gather_time
        self.hash_checker = HashChecker(hash_algo)
        self.pull = self.ctx.socket(zmq.PULL)
        log.info('{} PULL socket to {}',
                 'Binding' if pull_type == 'bind' else 'Connecting', pull_addr)
        getattr(self.pull, pull_type)(pull_addr)

        self.router = self.ctx.socket(zmq.ROUTER)
        log.info('{} ROUTER socket to {}',
                 'Binding' if router_type == 'bind' else 'Connecting', router_addr)
        getattr(self.router, router_type)(router_addr)

    def add_input(self, inp):
        pass

    def ready_to_process(self):
        return True

    def process(self):
        log.info('Process inputs')
        pass

    def reset_inputs(self):
        log.info('Resetting inputs')

    @property
    def condensed_output(self):
        return b''

    @property
    def commitment_data(self):
        return b''

    def recv_input(self):
        inp = self.pull.recv()
        log.debug('pull: recv -> {}'.format(inp.hex()))
        try:
            self.hash_checker.check(inp)
        except:
            log.warn('Bad hash received! -> {}', inp)
        else:
            self.add_input(inp)

    def recv_from_comp(self):
        compute_id, msg_type, status = self.router.recv_multipart()
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
            self.router.send_multipart([compute_id, MessageType.STATUS, Status.OK])
            if compute_id not in self.worker_deque:
                self.worker_deque.append(compute_id)
                log.info('Worker "{}" added to deque ({})', compute_id, len(self.worker_deque))
            log.debug('Worker "{}" already in deque ({})', compute_id, len(self.worker_deque))
        elif status == Status.OK:
            log.info('Worker "{}" received data', compute_id)
        elif status == Status.ERROR:
            log.warn('Worker "{}" reported error!', compute_id)


    def send_to_comp(self, compute_id, seq_no):
        # Send condensed input data, i.e. Merkle root
        self.router.send_multipart([
            compute_id,
            MessageType.INPUT,
            seq_no.to_bytes(2, byteorder='big'),
            self.condensed_output,
        ])
        log.debug('router: send to {} -> {} | {} | {}',
                  compute_id, MessageType.INPUT, seq_no, self.condensed_output.hex())

        # Send commitment data, i.e. leaves of Merkle tree
        data = self.commitment_data
        self.router.send_multipart([
            compute_id,
            MessageType.COMMIT,
            seq_no.to_bytes(2, byteorder='big'),
            data,
        ])
        log.debug('router: send to {} -> {} | {} | {}...',
                  compute_id, MessageType.COMMIT, seq_no, data.hex()[:20])

    def start_poll(self, start_seq_no=None):
        seq_no = start_seq_no if start_seq_no is not None else 0
        last_process = time.time()
        poller = Poller()
        poller.register(self.pull, zmq.POLLIN)
        poller.register(self.router, zmq.POLLIN)
        while True:
            try:
                socks = dict(poller.poll(timeout=self.gather_time * 100))
            except KeyboardInterrupt:
                return

            if self.pull in socks:
                self.recv_input()

            if self.router in socks:
                self.recv_from_comp()

            if self.worker_deque and self.ready_to_process() and time.time() - last_process >= self.gather_time:
                compute_id = self.worker_deque.popleft()
                last_process = time.time()
                try:
                    self.process()

                    self.send_to_comp(compute_id, seq_no)

                    self.reset_inputs()

                    if seq_no == 0xFFFF:
                        seq_no = 0
                    else:
                        seq_no += 1
                except Exception as e:
                    log.error("Could not process send and reset inputs -> {}".format(e))
            else:
                log.debug('time since last {}, deque size {}',
                          time.time() - last_process, len(self.worker_deque))

