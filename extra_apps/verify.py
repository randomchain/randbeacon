#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pprint import pprint
import click
import merkletools
import sloth
import msgpack
from randbeacon import utils
import ujson as json

SERIALIZED_FIELDS = ('COMMIT', 'PROOF')

def verify_sloth(inp, out, witness, bits, iterations):
    s = sloth.Sloth(data=inp,
                    final_hash=out,
                    witness=witness,
                    bits=bits,
                    iterations=iterations)
    s.verify()
    s.wait()
    return s.valid

def build_merkle_tree(leaves, hash_type, expected_root=None):
    mt = merkletools.MerkleTools(hash_type=hash_type)
    mt.leaves = leaves
    mt.make_tree()
    if expected_root is not None:
        assert mt.merkle_root == expected_root
        print("Root matches!")
    return mt

def unpack_sequence(json_file):
    beacon_sequence = json.load(json_file)
    for k, v in beacon_sequence.items():
        if k in SERIALIZED_FIELDS:
            beacon_sequence[k]['data'] = msgpack.unpackb(bytes.fromhex(v['data']))

    return beacon_sequence


@click.command()
@click.argument('json', type=click.File())
@click.option('--inp', type=str, default=None)
@click.option('--verbose', '-v', is_flag=True, default=False)
def main(json, inp, verbose):
    b_seq = unpack_sequence(json)
    print('\n\n {:=^50}\n'.format(" Sequence Data "))
    if verbose:
        pprint(b_seq, width=120)
    else:
        print("Sequence no.", b_seq['seq_no'])
        print("Output: {}\n{}".format(b_seq['OUTPUT']['data'], b_seq['OUTPUT']['timestamp']))
    commit_data = b_seq['COMMIT']['data']

    print('\n\n {:=^50}\n'.format(" Merkle Tree "))
    mt = build_merkle_tree(commit_data[b'leaves'], commit_data[b'hash_type'].decode('ascii'), commit_data[b'root'])
    print("Merkle Tree:\n\tRoot -> {}\n\tLeaves -> {}".format(mt.merkle_root.hex(), len(mt.leaves)))
    if inp:
        inp = bytes.fromhex(inp)
        try:
            idx = mt.leaves.index(inp)
        except ValueError:
            print("Input '{}' not found in commitment!".format(inp.hex()))
        else:
            print("Proof")
            pprint(mt.get_proof(idx))

    print('\n\n {:=^50}\n'.format(" Computation Verification "))
    proof_data = b_seq['PROOF']['data']
    print("Sloth parameters: {} bits, {} iterations".format(proof_data[b'bits'], proof_data[b'iterations']))
    print("Sloth witness: {}".format(proof_data[b'witness'].hex()))
    valid = verify_sloth(mt.merkle_root, bytes.fromhex(b_seq['OUTPUT']['data']), proof_data[b'witness'], proof_data[b'bits'], proof_data[b'iterations'])
    print("VALID" if valid else "NOT VALID!")

if __name__ == "__main__":
    main()
