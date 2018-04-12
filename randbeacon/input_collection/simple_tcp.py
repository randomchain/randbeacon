import hashlib
import sys
import threading
from queue import Queue
from socketserver import BaseRequestHandler, ThreadingTCPServer

import click
import zmq
from zmq import Context
from logbook import Logger, StreamHandler

StreamHandler(sys.stdout).push_application()
tcp_log = Logger('TCP Server')
push_log = Logger('Pusher')

ctx = Context.instance()
inp_queue = Queue()

PUSH_CONNECT = None
HASHER = None
TCP_HOST = None
TCP_PORT = None

class TCPInputRequestHandler(BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        tcp_log.debug("from {} -> {}".format(self.client_address[0], data))
        inp_hash = HASHER(data).digest()
        inp_queue.put(inp_hash)
        self.request.sendall(inp_hash)

def start_tcp():
    socketserver = ThreadingTCPServer((TCP_HOST, TCP_PORT), TCPInputRequestHandler)
    server_thread = threading.Thread(target=socketserver.serve_forever, daemon=True)
    server_thread.start()
    tcp_log.info("Running on {}:{}".format(*socketserver.server_address))

def start_pusher():
    push = ctx.socket(zmq.PUSH)
    push.connect(PUSH_CONNECT)
    push_log.info("Connected to {}".format(PUSH_CONNECT))
    while True:
        inp = inp_queue.get()
        push.send(inp)
        push_log.debug("send -> {}".format(inp))

@click.command()
@click.option('--hash-algo', default="sha512", help="Hashing algorithm to be used")
@click.option('--push-connect', default="tcp://localhost:11234", help="Addr of input processor")
@click.option('--tcp-host', default="0.0.0.0", help="Address of tcp host")
@click.option('--tcp-port', default=1337, help="Port of tcp")
def main(hash_algo, push_connect, tcp_host, tcp_port):
    global PUSH_CONNECT, HASHER, TCP_HOST, TCP_PORT
    PUSH_CONNECT = push_connect
    HASHER = getattr(hashlib, hash_algo)
    TCP_HOST = tcp_host
    TCP_PORT = tcp_port
    tcp_log.debug("Push address: {}, Hashing algorithm: {}, TCP host: {}, TCP port: {}".format(push_connect, hash_algo, tcp_host, tcp_port))

    start_tcp()
    start_pusher()

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_COLLECTOR_HTTP")
