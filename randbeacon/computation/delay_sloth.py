import time
import msgpack
from sloth import Sloth
import zmq
from zmq import Context
import click
from logbook import Logger, StreamHandler
import sys


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


def start_compute_loop(pub, pull, timeout=5):
    log.info("Starting compute loop")
    while True:
        log.info("publishing process message")
        pub.send_multipart([b'process', b'meme'])
        log.info("waiting {} seconds for incoming data".format(timeout))
        if pull.poll(timeout * 1000):
            header, seq_no_a, inp_data = pull.recv_multipart()
            log.info("recv -> {} | {} | {}".format(header, seq_no_a, inp_data))
            if header != b'\x01':
                log.error("Expected to receive compute data, not commitment")
                return
            header, seq_no_b, commit_data = pull.recv_multipart()
            commit_data = msgpack.unpackb(commit_data)
            log.info("recv -> {} | {} | merkle height {}".format(header, seq_no_b, len(commit_data)))
            if header != b'\x02':
                log.error("Expected to receive commitment, not compute data")
                return
            if seq_no_a != seq_no_b:
                log.error("Got unpaired sequence numbers!")
                return
            # forward commitment to publisher

            # in the future we may want to change the order at which this happens
            sloth = init_compute(inp_data)
            sloth.wait()
            log.info(" === OUTPUT --> {} === ".format(sloth.final_hash))
            log.info(" === WITNESS --> {} === ".format(sloth.witness))



@click.command()
@click.option('--pull-bind', default="tcp://*:11234", help="Pull socket bind")
@click.option('--pub-bind', default="tcp://*:23456", help="Publish socket bind")
@click.option('--sloth-bits', default=2048, help="Bits for sloth prime")
@click.option('--sloth-iterations', default=5000, help="Iterations of permutation in sloth")
def main(pull_bind, pub_bind, sloth_bits, sloth_iterations):
    global SLOTH_BITS, SLOTH_ITERATIONS

    SLOTH_BITS = sloth_bits
    SLOTH_ITERATIONS = sloth_iterations

    pull = ctx.socket(zmq.PULL)
    pull.bind('tcp://*:11234')

    pub = ctx.socket(zmq.PUB)
    pub.bind('tcp://*:23456')

    time.sleep(1)
    start_compute_loop(pub, pull)


if __name__ == "__main__":
    main(auto_envvar_prefix="COMPUTATION_SLOTH")
