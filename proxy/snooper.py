import zmq
from zmq import Context
import sys

ctx = Context()

sub = ctx.socket(zmq.SUB)
sub.connect(sys.argv[1])
sub.setsockopt(zmq.SUBSCRIBE, b'')

i = 0
while True:
    recv = sub.recv_multipart()
    if len(sys.argv) > 2 and sys.argv[2] == '-v':
        print("{:6} | ({}) {}".format(i, len(recv), repr(recv)))
    else:
        print("{:6} | ({}) {:.200}...".format(i, len(recv), repr(recv)))
    i += 1
