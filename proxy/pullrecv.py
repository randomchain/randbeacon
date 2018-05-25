import zmq
from zmq import Context
import sys
import time

ctx = Context()

pull = ctx.socket(zmq.PULL)
pull.connect(sys.argv[1])

time.sleep(1)

gosub = ctx.socket(zmq.SUB)
gosub.connect(sys.argv[2])
gosub.setsockopt(zmq.SUBSCRIBE, b'')

gosub.recv_multipart()
gosub.close()
i = 0
t0 = time.time()
while True:
    pull.recv()
    print("{:6} : {:.2} msg/s".format(i, i / (time.time() - t0)))
    i += 1

