from socketserver import ThreadingTCPServer, BaseRequestHandler
import threading
import time
from queue import Queue
from . import BaseInputCollector

INPUTS = []

class TCPInputRequestHandler(BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        print("from {}\n -> {}".format(self.client_address[0], data))
        INPUTS.append(data)
        self.request.sendall(b"OK\0")

class SimpleTCPInputCollector(BaseInputCollector):

    def __init__(self, host="localhost", port=1337):
        self.inputs = []
        self.host = host
        self.port = port

    def collect(self, duration=None):
        self.socketserver = ThreadingTCPServer((self.host, self.port), TCPInputRequestHandler)
        self.server_thread = threading.Thread(target=self.socketserver.serve_forever, daemon=True)
        self.server_thread.start()
        print("Running TCP server on {}:{}".format(*self.socketserver.server_address))
        time.sleep(duration)
        self.socketserver.shutdown()
        self.socketserver.server_close()

    @property
    def collected_inputs(self):
        self.inputs[:] = INPUTS
        INPUTS.clear()
        return iter(self.inputs)
