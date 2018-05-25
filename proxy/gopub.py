import zmq
from zmq import Context
import sys

ctx = Context()

pub = ctx.socket(zmq.PUB)
pub.bind(sys.argv[1])

input("hit enter to publish go msg")
pub.send_multipart([b"", b"here we gooo"])
