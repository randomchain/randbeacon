import threading
import time, os
#from queue import Queue
from . import BaseInputCollector
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

class TelegramInputCollector(BaseInputCollector):

    def __init__(self):
        self.inputs = []
        self.apitoken = os.environ['TELEGRAM_API']

    def start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Any message you send to me will be included as input to the next beacon output.")

    def echo(self, bot, update):
        self.inputs.append(update.message.text)
        print("Telegram:", update.message.text)
        bot.send_message(chat_id=update.message.chat_id, text="Thank you for your input!")

    def collect(self, duration=None):
        # Source: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-–-Your-first-Bot
        updater = Updater(token=self.apitoken)
        dispatcher = updater.dispatcher
        start_handler = CommandHandler('start', self.start)
        echo_handler = MessageHandler(Filters.text, self.echo)
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(echo_handler)
        updater.start_polling()
        time.sleep(duration)
        updater.stop()

    @property
    def collected_inputs(self):
        return iter(self.inputs)
