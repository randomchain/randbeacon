import tweepy
import zmq
from zmq import Context
import logbook
from credentials import *

sub_connect = "tcp://localhost:33456"
ctx = Context.instance()

def main():

    #Tweepy: Authentication and initialization of API
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    #ZMQ, initialize subcription (God knows if it works)
    sub = ctx.socket(zmq.SUB)
    sub.connect(sub_connect)
    sub.setsockopt(zmq.SUBSCRIBE, b'\x03')

    #Wait for inputs
    while True:
        input = sub.recv_multipart()
        #On receive, tweet sequence number followed by data. 
        api.update_status("No. {num} - {rand}".format(num = input[0], rand = input[1]) )

if  __name__ == "__main__":
    main()