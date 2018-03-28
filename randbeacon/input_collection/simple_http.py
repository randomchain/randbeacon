from asyncio import Queue
from sanic import Sanic, response
from zmq.asyncio import Context
import zmq
import click


ctx = Context.instance()
app = Sanic()
input_queue = None
PUSH_CONNECT = None


async def push_loop():
    push = ctx.socket(zmq.PUSH)
    while True:
        inp = await input_queue.get()
        push.connect(PUSH_CONNECT)
        await push.send(inp)


@app.route("/", methods=["POST", ])
async def give_input(request):
    if request.body:
        await input_queue.put(request.body)
        return response.raw(request.body, status=200)
    return response(status=400)


@app.listener('after_server_start')
async def init_queue_and_zmq(app, loop):
    global input_queue
    input_queue = Queue(loop=loop)
    await push_loop()


@click.command()
@click.option('--push-connect', default="tcp://localhost:12345", help="Addr of input processor")
@click.option('--http-host', default="0.0.0.0", help="Host of http server")
@click.option('--http-port', default=8080, help="Port of http server")
def main(push_connect, http_host, http_port):
    global PUSH_CONNECT
    PUSH_CONNECT = push_connect

    app.run(http_host, http_port, debug=False)


if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_COLLECTOR_HTTP")
