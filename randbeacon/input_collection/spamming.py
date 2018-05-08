import hashlib
import sys
import time
import click
from logbook import Logger, StreamHandler
import zmq
from zmq import Context

StreamHandler(sys.stdout).push_application()
log = Logger('spamming collector')
ctx = Context()

STATIC_HASH = None


def push_loop(push_connect, hasher, spam_interval, random):
    push = ctx.socket(zmq.PUSH)
    push.connect(push_connect)
    while True:
        if random:
            inp_hash = hasher(str(time.time()).encode('ascii')).digest()
        else:
            inp_hash = STATIC_HASH
        push.send(inp_hash)
        log.debug('send -> {}'.format(inp_hash.hex()))
        time.sleep(spam_interval)

@click.command()
@click.option('--hash-algo', default="sha512", help="Hashing algorithm to be used")
@click.option('--push-connect', default="tcp://localhost:11234", help="Addr of input processor")
@click.option('--spam-interval', default=1.0, help="The spam interval in seconds")
@click.option('--random', default=False, is_flag=True)
def main(hash_algo, push_connect, spam_interval, random):
    global STATIC_HASH
    hasher = getattr(hashlib, hash_algo)
    if not random:
        STATIC_HASH = hasher(str(time.time()).encode('ascii')).digest()

    log.debug("Address: {}, Hashing algorithm: {}, Spam interval: {}, inp hash: {}",
              push_connect, hash_algo, spam_interval, 'random' if random else 'static')

    push_loop(push_connect, hasher, spam_interval, random)

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_COLLECTOR_SPAM")

