import hashlib
import sys
import time
from os import urandom
import click
from logbook import Logger, StreamHandler
import zmq
from zmq import Context

StreamHandler(sys.stdout).push_application()
log = Logger('urandom collector')

PUSH_CONNECT = None
HASHER = None
RANDOM_BYTES = None
PUSH_INTERVAL = None
ctx = Context()

def push_loop():
    push = ctx.socket(zmq.PUSH)
    push.connect(PUSH_CONNECT)
    while True:
        inp = urandom(RANDOM_BYTES)
        inp_hash = HASHER(inp).digest()
        push.send(inp_hash)
        log.info('send -> {}'.format(inp_hash.hex()))
        time.sleep(PUSH_INTERVAL)

@click.command()
@click.option('--hash-algo', default="sha512", help="Hashing algorithm to be used")
@click.option('--push-connect', default="tcp://localhost:11234", help="Addr of input processor")
@click.option('--push-interval', default=5, help="The push interval in seconds")
@click.option('--random-bytes', default=64, help="The number of bytes to get from urandom")
def main(hash_algo, push_connect, push_interval, random_bytes):
    global PUSH_CONNECT, HASHER, PUSH_INTERVAL, RANDOM_BYTES
    PUSH_CONNECT = push_connect
    HASHER = getattr(hashlib, hash_algo)
    PUSH_INTERVAL = push_interval
    RANDOM_BYTES = random_bytes
    log.debug("Address: {}, Hashing algorithm: {}, Push interval: {}, Random bytes: {}".format(push_connect, hash_algo, push_interval, random_bytes))

    push_loop()

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_COLLECTOR_HTTP")
