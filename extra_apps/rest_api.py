"""Very simple REST api for browsing beacon sequences"""
import hug
from json_read import read_seq_no


@hug.get('/seq/{seq_no}', versions=1)
def sequence(seq_no, parse=True):
    return read_seq_no(seq_no, parse=parse)

