import hashlib
from os import urandom
import sys
import time
import zmq
from zmq import Context
from logbook import StreamHandler, Logger

StreamHandler(sys.stdout).push_application()
log = Logger('urandom coll.')

hasher = hashlib.sha512
ctx = Context()
push = ctx.socket(zmq.PUSH)
push.connect('tcp://localhost:12345')

RANDOM_BYTES = 512
PUSH_INTERVAL = 5

while True:
    inp = urandom(RANDOM_BYTES)
    inp_hash = hasher(inp).digest()
    push.send(inp_hash)
    log.info('send -> {}...'.format(inp_hash.hex()))
    time.sleep(PUSH_INTERVAL)

