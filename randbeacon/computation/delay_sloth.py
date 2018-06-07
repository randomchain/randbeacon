import time
import sys
import msgpack
from sloth import Sloth
import zmq
from zmq import Context
import click
from logbook import Logger, StreamHandler
from .base import BaseComputation


log = Logger("CompSloth")


class SlothComputation(BaseComputation):

    def __init__(self, *, sloth_bits, sloth_iterations, **kwargs):
        super().__init__(**kwargs)
        self._sloth_bits = sloth_bits
        self._sloth_iterations = sloth_iterations
        self.sloth = Sloth(
            data=None, bits=sloth_bits, iterations=sloth_iterations
        )

    def start_computation(self, inp_data):
        self.sloth.final_hash = None
        self.sloth.witness = None
        self.sloth.data = inp_data
        log.info(
            "Starting Sloth computation - bits: {}, iterations: {}",
            self.sloth.bits,
            self.sloth.iterations,
        )
        self.sloth.compute()

    def finish_computation(self):
        self.sloth.wait()
        self.output = self.sloth.final_hash
        log.info(" === OUTPUT --v\n{}\n === ", self.sloth.final_hash)
        log.info(" === WITNESS --v\n{}\n === ", self.sloth.witness)

    @property
    def proof(self):
        return msgpack.packb(
            {
                "witness": self.sloth.witness,
                "bits": self.sloth.bits,
                "iterations": self.sloth.iterations,
            }
        )

    @proof.setter
    def proof(self, value):
        return None


@click.command()
@click.option("--identity", default=None, help="identity")
@click.option(
    "--dealer-connect", default="tcp://localhost:22345", help="dealer connect address"
)
@click.option("--pub-addr", default="tcp://*:44567", help="Publish socket address")
@click.option(
    "--pub-type",
    type=click.Choice(["bind", "connect"]),
    default="bind",
    help="Publish socket type",
)
@click.option("--sloth-bits", default=2048, help="Bits for sloth prime")
@click.option(
    "--sloth-iterations", default=5000, help="Iterations of permutation in sloth"
)
@click.option("-v", "--verbose", is_flag=True, default=False)
def main(
    identity, dealer_connect, pub_addr, pub_type, sloth_bits, sloth_iterations, verbose
):
    StreamHandler(sys.stdout, level="DEBUG" if verbose else "INFO").push_application()

    sloth_compute = SlothComputation(
        dealer_connect=dealer_connect,
        pub_addr=pub_addr,
        pub_type=pub_type,
        timeout=10,
        identity=identity,
        sloth_bits=sloth_bits,
        sloth_iterations=sloth_iterations,
    )
    time.sleep(1)
    sloth_compute.start_compute_loop()


if __name__ == "__main__":
    main(auto_envvar_prefix="COMPUTATION_SLOTH")
