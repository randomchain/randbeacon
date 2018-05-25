import zmq
from zmq import Context
import sys
import time

ctx = Context()

push = ctx.socket(zmq.PUSH)
push.connect(sys.argv[1])

time.sleep(1)

gosub = ctx.socket(zmq.SUB)
gosub.connect(sys.argv[2])
gosub.setsockopt(zmq.SUBSCRIBE, b"")

gosub.recv_multipart()
gosub.close()
i = 0
t0 = time.time()
while True:
    push.send(b"memes", copy=False, track=True).wait()
    i += 1
    print("{:6} : {:.2} msg/s".format(i, i / (time.time() - t0)))
