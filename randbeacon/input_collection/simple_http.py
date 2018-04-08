import hashlib
import sys
from asyncio import Queue
from sanic import Sanic, response
from zmq.asyncio import Context
import zmq
import click
from logbook import Logger, StreamHandler

StreamHandler(sys.stdout).push_application()
log = Logger('input')

ctx = Context.instance()
app = Sanic()
input_queue = None
PUSH_CONNECT = None
HASHER = None


async def push_loop():
    push = ctx.socket(zmq.PUSH)
    push.connect(PUSH_CONNECT)
    while True:
        inp = await input_queue.get()
        await push.send_multipart([b'\x01', inp])


@app.route("/", methods=["POST", ])
async def give_input(request):
    if request.json:
        inp_bytes = b''
        for encoding, inp_str in request.json.items():
            try:
                if encoding == 'hex':
                    inp_bytes += bytes.fromhex(inp_str)
                else:
                    inp_bytes += inp_str.encode(encoding)
                log.debug("enc -> {}, value -> {}".format(encoding, inp_str[:20]))
            except Exception as e:
                log.error(e)
                return response.json({'message': "Invalid encoding-data_string pair"}, status=400)
        inp_hash = HASHER(inp_bytes).digest()
        await input_queue.put(inp_hash)
        inp_hash_hex = inp_hash.hex()
        log.info("hash -> {}".format(inp_hash_hex))
        return response.json(
                {
                    'message': "Input received",
                    'hash': inp_hash_hex,
                },
                status=200)
    return response.json({'message': "No input provided"}, status=400)


@app.listener('after_server_start')
async def init_queue_and_zmq(app, loop):
    global input_queue
    input_queue = Queue(loop=loop)
    await push_loop()


@click.command()
@click.option('--hash-algo', default="sha512", help="Hashing algorithm to be used")
@click.option('--push-connect', default="tcp://localhost:12345", help="Addr of input processor")
@click.option('--http-host', default="0.0.0.0", help="Host of http server")
@click.option('--http-port', default=8080, help="Port of http server")
def main(hash_algo, push_connect, http_host, http_port):
    global PUSH_CONNECT, HASHER
    PUSH_CONNECT = push_connect
    HASHER = getattr(hashlib, hash_algo)
    log.info("hashing algo: {}".format(hash_algo))

    app.run(http_host, http_port, debug=False)


if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_COLLECTOR_HTTP")
