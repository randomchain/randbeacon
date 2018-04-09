import hashlib
import threading
import time, os
#from queue import Queue
import zmq
from zmq import Context
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

API_TOKEN = os.environ['TELEGRAM_API']

updater = Updater(token=API_TOKEN)

hasher = hashlib.sha512
ctx = Context()
push = ctx.socket(zmq.PUSH)
push.connect('tcp://localhost:12345')

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Any message you send to me will be included as input to the next beacon output.")

start_handler = CommandHandler('start', start)

def get_input(bot, update):
    inp_hash = hasher(update.message.text.encode('utf-8')).digest()
    print("Telegram Received:", update.message.text)
    push.send(inp_hash)
    print("send -> {}".format(inp_hash.hex()))
    bot.send_message(chat_id=update.message.chat_id, text="Thank you for your input!\n{}".format(inp_hash.hex()))

input_handler = MessageHandler(Filters.text, get_input)
updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(input_handler)

try:
    updater.start_polling()
    print("Running Telegram Bot")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    updater.stop()

