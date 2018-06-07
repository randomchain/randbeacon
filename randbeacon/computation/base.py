import time
import sys
import zmq
from zmq import Context
from logbook import Logger, StreamHandler
from ..utils import MessageType, Status, HashChecker


log = Logger("Comp")


class BaseComputation:

    def __init__(
        self, *, dealer_connect, pub_addr, pub_type, timeout=10, identity=None, **kwargs
    ):
        self.ctx = Context.instance()
        if identity is None:
            import os
            self.identity = os.getpid().to_bytes(3, byteorder="big")
            log.debug("Got no identity. Using PID {}", identity)
        else:
            self.identity = identity
        self.timeout = timeout

        log.info("Connecting dealer to {}, with identity {}", dealer_connect, self.identity)
        self.dealer = self.ctx.socket(zmq.DEALER)
        self.dealer.setsockopt(zmq.IDENTITY, self.identity)
        self.dealer.connect(dealer_connect)

        self.pub = self.ctx.socket(zmq.PUB)
        getattr(self.pub, pub_type)(pub_addr)

        self.output = None
        self.proof = None

    def start_computation(self, inp_data):
        log.info("Start computation")

    def finish_computation(self):
        log.info("Wait for computation to finish")

    def recv_message(self, expected_header, expected_data_len):
        if not self.dealer.poll(self.timeout * 1000):
            raise Exception("Timeout while waiting to receive " + expected_header.name)
        header, *data = self.dealer.recv_multipart()
        header = MessageType(header)
        log.info(
            "recv -> {} | ({}) {}",
            header.name,
            len(data),
            " | ".join([str(d) for d in data]),
        )
        if header != expected_header or len(data) != expected_data_len:
            self.dealer.send_multipart([MessageType.STATUS, Status.ERROR])
            raise Exception(
                "Expected to receive "
                + expected_header.name
                + " with data len "
                + str(expected_data_len)
            )
        return data

    def start_compute_loop(self):
        log.info("Starting compute loop")
        while True:
            log.info("Sending 'ready' message")
            self.dealer.send_multipart([MessageType.STATUS, Status.READY])
            log.info("waiting {} seconds for OK", self.timeout)
            if self.dealer.poll(self.timeout * 1000):
                try:
                    status, = self.recv_message(MessageType.STATUS, 1)
                    if status != Status.OK:
                        raise Exception(
                            "Got unexpected status from input processor " + str(status)
                        )

                    seq_no_a, inp_data = self.recv_message(MessageType.INPUT, 2)
                    seq_no_b, commit_data = self.recv_message(MessageType.COMMIT, 2)
                    # TODO: check commitment?

                    if seq_no_a != seq_no_b:
                        raise Exception("Got unpaired sequence numbers!")
                except Exception as e:
                    log.warn("Message error -> {}", e)
                    self.dealer.send_multipart([MessageType.STATUS, Status.ERROR])
                    continue

                self.dealer.send_multipart([MessageType.STATUS, Status.OK])

                self.start_computation(inp_data)

                self.pub.send_multipart([MessageType.COMMIT, seq_no_b, commit_data])

                self.finish_computation()

                self.pub.send_multipart([MessageType.OUTPUT, seq_no_b, self.output])
                self.pub.send_multipart([MessageType.PROOF, seq_no_b, self.proof])
