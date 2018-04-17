import zmq
from zmq import Context
import sys

ctx = Context()

sub = ctx.socket(zmq.SUB)
sub.connect(sys.argv[1])
sub.setsockopt(zmq.SUBSCRIBE, b'')

while True:
    print(sub.recv_multipart())
