import sys
import tweepy
import zmq
from logbook import Logger, StreamHandler
import click
from .credentials import *

@click.command()
@click.option('--sub-connect', default="tcp://localhost:44567")
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-d", "--delete", is_flag=True, default=False)
def main(sub_connect, verbose, delete):
    StreamHandler(sys.stdout, level="DEBUG" if verbose else "INFO").push_application()
    log = Logger('twitter')

    ctx = zmq.Context.instance()
    #Tweepy: Authentication and initialization of API
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    log.info('Bot connected to twitter')

    if delete:
        log.info('Removing all previous tweets')
        for status in tweepy.Cursor(api.user_timeline).items():
            try:
                api.destroy_status(status.id)
                log.info('Deleted {}', status.id)
            except:
                log.warn('Failed to delete {}', status.id)

    #ZMQ - initialize subcription to port and message type.
    log.info('Connecting SUB socket to {}' .format(sub_connect))
    sub = ctx.socket(zmq.SUB)
    sub.connect(sub_connect)
    sub.setsockopt(zmq.SUBSCRIBE, b'\x03')

    #Wait for messages
    while True:
        _, seq_no, output = sub.recv_multipart()
        seq_no = int.from_bytes(seq_no, byteorder='big')
        log.debug('recv -> {} | {}', seq_no, output)
        log.info('Publishing tweet for seq no {}', seq_no)
        #On receive, tweet sequence number followed by data.
        api.update_status("Output #{} {}".format(seq_no, output.hex()))

if  __name__ == "__main__":
    main()
