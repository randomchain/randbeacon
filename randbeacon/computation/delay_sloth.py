import time
import sys
import msgpack
from sloth import Sloth
import zmq
from zmq import Context
import click
from logbook import Logger, StreamHandler
from ..utils import MessageType, HashChecker


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


def start_compute_loop(process_pub, pub, pull, timeout=5):
    log.info("Starting compute loop")
    while True:
        log.info("publishing process message")
        process_pub.send_multipart([b'process', b'meme'])
        log.info("waiting {} seconds for incoming data".format(timeout))
        if pull.poll(timeout * 1000):
            header, seq_no_a, inp_data = pull.recv_multipart()
            header = MessageType(header)
            log.info("recv -> {} | {} | {}".format(header.name, seq_no_a, inp_data))
            if header != MessageType.INPUT:
                log.error("Expected to receive compute data, not commitment")
                return
            header, seq_no_b, commit_data = pull.recv_multipart()
            header = MessageType(header)
            commit_data_obj = msgpack.unpackb(commit_data)
            log.info("recv -> {} | {} | merkle height {}".format(header.name, seq_no_b, len(commit_data_obj)))
            if header != MessageType.COMMIT:
                log.error("Expected to receive commitment, not compute data")
                return
            if seq_no_a != seq_no_b:
                log.error("Got unpaired sequence numbers!")
                return
            sloth = init_compute(inp_data)
            pub.send_multipart([header.value, seq_no_b, commit_data])
            sloth.wait()
            pub.send_multipart([MessageType.OUTPUT.value, seq_no_b, sloth.final_hash])
            pub.send_multipart([MessageType.PROOF.value, seq_no_b, sloth.witness])
            log.info(" === OUTPUT --> {} === ".format(sloth.final_hash))
            log.info(" === WITNESS --> {} === ".format(sloth.witness))



@click.command()
@click.option('--pull-bind', default="tcp://*:22345", help="Pull socket bind")
@click.option('--pub-addr', default="tcp://*:44567", help="Publish socket address")
@click.option('--pub-type', type=click.Choice(['bind', 'connect']), default='bind', help="Publish socket type")
@click.option('--process-pub-bind', default="tcp://*:33456", help="Input processor Publish socket bind")
@click.option('--sloth-bits', default=2048, help="Bits for sloth prime")
@click.option('--sloth-iterations', default=5000, help="Iterations of permutation in sloth")
def main(pull_bind, pub_addr, pub_type, process_pub_bind, sloth_bits, sloth_iterations):
    global SLOTH_BITS, SLOTH_ITERATIONS

    SLOTH_BITS = sloth_bits
    SLOTH_ITERATIONS = sloth_iterations

    pull = ctx.socket(zmq.PULL)
    pull.bind(pull_bind)

    process_pub = ctx.socket(zmq.PUB)
    process_pub.bind(process_pub_bind)

    pub = ctx.socket(zmq.PUB)
    getattr(pub, pub_type)(pub_addr)

    time.sleep(1)
    start_compute_loop(process_pub, pub, pull)


if __name__ == "__main__":
    main(auto_envvar_prefix="COMPUTATION_SLOTH")
