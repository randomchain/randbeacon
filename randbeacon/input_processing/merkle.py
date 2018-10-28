import sys
import click
import msgpack
from logbook import Logger, StreamHandler
from merkletools import MerkleTools
from .base import BaseInputProcessor

log = Logger('Merkle')


class MerkleInputProcessor(BaseInputProcessor):
    def __init__(self, *, hash_algo, **kwargs):
        super().__init__(hash_algo=hash_algo, **kwargs)
        self.mt = MerkleTools(hash_type=hash_algo)
        log.info('Tree using {} hashing algorithm', hash_algo)

    def add_input(self, inp):
        self.mt.add_leaf(inp, do_hash=False)
        log.info('leaf added | leaves: {}'.format(len(self.mt.leaves)))

    def ready_to_process(self):
        return len(self.mt.leaves) > 0

    def process(self):
        log.info('Make Tree')
        self.mt.make_tree()
        log.info('Merkle root {}', self.mt.merkle_root.hex())

    def reset_inputs(self):
        self.mt.reset_tree()
        log.info('Resetting Merkle Tree')

    @property
    def condensed_output(self):
        return self.mt.merkle_root

    @property
    def commitment_data(self):
        return msgpack.packb({'root': self.mt.merkle_root, 'leaves': self.mt.leaves, 'hash_type': self.mt._hash_type})


@click.command()
@click.option('--hash-algo', default="sha512")
@click.option('--gather-time', default=5.0)
@click.option('--pull-addr', default="tcp://*:11234")
@click.option('--pull-type', type=click.Choice(['bind', 'connect']), default='bind')
@click.option('--router-addr', default="tcp://*:22345")
@click.option('--router-type', type=click.Choice(['bind', 'connect']), default='bind')
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(hash_algo, gather_time, pull_addr, pull_type, router_addr, router_type, verbose):
    StreamHandler(sys.stdout, level='DEBUG' if verbose else 'INFO').push_application()
    merkle_processor = MerkleInputProcessor(
        pull_addr=pull_addr,
        pull_type=pull_type,
        router_addr=router_addr,
        router_type=router_type,
        gather_time=gather_time,
        hash_algo=hash_algo)

    merkle_processor.start_poll()

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_PROCESSOR_MERKLE")

