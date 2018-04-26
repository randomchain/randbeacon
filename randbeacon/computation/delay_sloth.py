import time
import sys
import msgpack
from sloth import Sloth
import zmq
from zmq import Context
import click
from logbook import Logger, StreamHandler
from ..utils import MessageType, Status, HashChecker


StreamHandler(sys.stdout).push_application()
log = Logger('CompSloth')
ctx = Context.instance()
SLOTH_BITS = None
SLOTH_ITERATIONS = None


def init_compute(inp_data):
    sloth = Sloth(
        data=inp_data,
        bits=SLOTH_BITS,
        iterations=SLOTH_ITERATIONS
    )
    log.info("Starting Sloth computation - bits: {}, iterations: {}".format(SLOTH_BITS, SLOTH_ITERATIONS))
    sloth.compute()
    return sloth


def start_compute_loop(dealer, pub, timeout=5):
    log.info("Starting compute loop")
    while True:
        log.info("Sending 'ready' message")
        dealer.send_multipart([MessageType.STATUS, Status.READY])
        log.info("waiting {} seconds for OK".format(timeout))
        if dealer.poll(timeout * 1000):
            msg_type, status = dealer.recv_multipart()
            if msg_type != MessageType.STATUS or status != Status.OK:
                continue
            header, seq_no_a, inp_data = dealer.recv_multipart()
            header = MessageType(header)
            log.info("recv -> {} | {} | {}".format(header.name, seq_no_a, inp_data))
            if header != MessageType.INPUT:
                dealer.send_multipart([MessageType.STATUS, Status.ERROR])
                log.error("Expected to receive compute data, not commitment")
                return
            header, seq_no_b, commit_data = dealer.recv_multipart()
            header = MessageType(header)
            commit_data_obj = msgpack.unpackb(commit_data)
            log.info("recv -> {} | {} | leaves {}".format(header.name, seq_no_b, len(commit_data_obj)))
            if header != MessageType.COMMIT:
                dealer.send_multipart([MessageType.STATUS, Status.ERROR])
                log.error("Expected to receive commitment, not compute data")
                return
            if seq_no_a != seq_no_b:
                dealer.send_multipart([MessageType.STATUS, Status.ERROR])
                log.error("Got unpaired sequence numbers!")
                return
            dealer.send_multipart([MessageType.STATUS, Status.OK])
            sloth = init_compute(inp_data)
            pub.send_multipart([header, seq_no_b, commit_data])
            sloth.wait()
            pub.send_multipart([MessageType.OUTPUT, seq_no_b, sloth.final_hash])
            pub.send_multipart([MessageType.PROOF, seq_no_b, sloth.witness])
            log.info(" === OUTPUT --> {} === ".format(sloth.final_hash))
            log.info(" === WITNESS --> {} === ".format(sloth.witness))



@click.command()
@click.option('--identity', default=None, help="identity")
@click.option('--dealer-connect', default="tcp://localhost:22345", help="dealer connect address")
@click.option('--pub-addr', default="tcp://*:44567", help="Publish socket address")
@click.option('--pub-type', type=click.Choice(['bind', 'connect']), default='bind', help="Publish socket type")
@click.option('--sloth-bits', default=2048, help="Bits for sloth prime")
@click.option('--sloth-iterations', default=5000, help="Iterations of permutation in sloth")
def main(identity, dealer_connect, pub_addr, pub_type, sloth_bits, sloth_iterations):
    global SLOTH_BITS, SLOTH_ITERATIONS

    SLOTH_BITS = sloth_bits
    SLOTH_ITERATIONS = sloth_iterations

    if identity is None:
        import os
        identity = os.getpid().to_bytes(3, byteorder='big')
        log.debug("Got no identity. Using PID {}", identity)
    log.info("Connecting dealer to {}, with identity {}", dealer_connect, identity)
    dealer = ctx.socket(zmq.DEALER)
    dealer.setsockopt(zmq.IDENTITY, identity)
    dealer.connect(dealer_connect)

    pub = ctx.socket(zmq.PUB)
    getattr(pub, pub_type)(pub_addr)

    time.sleep(1)
    start_compute_loop(dealer, pub)


if __name__ == "__main__":
    main(auto_envvar_prefix="COMPUTATION_SLOTH")
