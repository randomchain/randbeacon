import hashlib
from socketserver import ThreadingTCPServer, BaseRequestHandler
import threading
from queue import Queue
import sys
from logbook import Logger, StreamHandler
import zmq
from zmq import Context

StreamHandler(sys.stdout).push_application()
tcp_log = Logger('TCP Server')
push_log = Logger('Pusher')

ctx = Context.instance()
inp_queue = Queue()
hasher = hashlib.sha512

class TCPInputRequestHandler(BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        tcp_log.debug("from {} -> {}".format(self.client_address[0], data))
        inp_hash = hasher(data).digest()
        inp_queue.put(inp_hash)
        self.request.sendall(inp_hash)

def start_tcp():
    socketserver = ThreadingTCPServer(("0.0.0.0", 1337), TCPInputRequestHandler)
    server_thread = threading.Thread(target=socketserver.serve_forever, daemon=True)
    server_thread.start()
    tcp_log.info("Running on {}:{}".format(*socketserver.server_address))

def start_pusher():
    push = ctx.socket(zmq.PUSH)
    push.connect('tcp://localhost:12345')
    push_log.info("Connected to {}:{}".format("localhost", 23456))
    while True:
        inp = inp_queue.get()
        push.send(inp)
        push_log.debug("send -> {}".format(inp))

start_tcp()
start_pusher()
