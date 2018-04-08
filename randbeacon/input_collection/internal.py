from os import urandom
import sys
import time
import zmq
from zmq import Context
from logbook import StreamHandler, Logger

StreamHandler(sys.stdout).push_application()
log = Logger('urandom coll.')

ctx = Context()
push = ctx.socket(zmq.PUSH)
push.connect('tcp://localhost:12345')

RANDOM_BYTES = 512
PUSH_INTERVAL = 5

while True:
    inp = urandom(RANDOM_BYTES)
    push.send_multipart([b'\x00', inp])
    log.info('send -> {}...'.format(inp[:20].hex()))
    time.sleep(PUSH_INTERVAL)

