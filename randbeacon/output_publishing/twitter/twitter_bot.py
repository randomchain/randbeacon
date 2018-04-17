import sys
import tweepy
import zmq
from zmq import Context
import logbook
from logbook import Logger, StreamHandler
from credentials import *

#Logbook setup
StreamHandler(sys.stdout, level=logbook.INFO).push_application()
log = Logger('twitter bot')

#ZMQ Constants
sub_connect = "tcp://localhost:33456"
ctx = Context.instance()

def main():

    #Tweepy: Authentication and initialization of API
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    log.info('Bot connected to twitter')

    #ZMQ - initialize subcription to port and message type.
    log.info('Connecting SUB socket to {}' .format(sub_connect))
    sub = ctx.socket(zmq.SUB)
    sub.connect(sub_connect)
    sub.setsockopt(zmq.SUBSCRIBE, b'\x03')

    #Wait for messages
    while True:
        msg = sub.recv_multipart()
        log.info('recv -> {}'.format(msg))
        #On receive, tweet sequence number followed by data.
        api.update_status("No. {num} - {rand}".format(num=msg[0], rand=msg[1]))

if  __name__ == "__main__":
    main()
