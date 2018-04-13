import hashlib
import os
import sys
import threading
import time
from functools import partial
import click
import zmq
from logbook import Logger, StreamHandler
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

StreamHandler(sys.stdout).push_application()
logger = Logger('Telegram')

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Any message you send to me will be included as input to the next beacon output.")

def get_input(push, hasher, bot, update):
    inp_hash = hasher(update.message.text.encode('utf-8')).digest()
    logger.info("Telegram Received: {}", update.message.text)
    push.send(inp_hash)
    logger.debug("send -> {}", inp_hash.hex())
    bot.send_message(chat_id=update.message.chat_id, text="Thank you for your input!\n{}".format(inp_hash.hex()))

@click.command()
@click.option('--hash-algo', default="sha512", help="Hashing algorithm to be used")
@click.option('--push-connect', default="tcp://localhost:11234", help="Addr of input processor")
@click.option('--telegram-apikey', envvar='TELEGRAM_API', help="Telegram bot api key")
def main(hash_algo, push_connect, telegram_apikey):
    hasher = getattr(hashlib, hash_algo)
    logger.debug("Push address: {}, Hashing algorithm: {}", push_connect, hash_algo)

    ctx = zmq.Context()
    push = ctx.socket(zmq.PUSH)
    push.connect(push_connect)

    updater = Updater(token=telegram_apikey)
    start_handler = CommandHandler('start', start)
    input_handler = MessageHandler(Filters.text, partial(get_input, push, hasher))
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(input_handler)

    updater.start_polling()
    logger.info("Running Telegram Bot")
    updater.idle()

if __name__ == "__main__":
    main(auto_envvar_prefix="INPUT_COLLECTOR_TELEGRAM")
