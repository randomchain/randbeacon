import threading
import time, os
#from queue import Queue
from . import BaseInputCollector
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

class TelegramInputCollector(BaseInputCollector):

    def __init__(self):
        self.inputs = []
        self.apitoken = os.environ['TELEGRAM_API']
        self.updater = Updater(token=self.apitoken)
        start_handler = CommandHandler('start', self.start)
        input_handler = MessageHandler(Filters.text, self.get_input)
        self.updater.dispatcher.add_handler(start_handler)
        self.updater.dispatcher.add_handler(input_handler)

    def start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Any message you send to me will be included as input to the next beacon output.")

    def get_input(self, bot, update):
        self.inputs.append(update.message.text)
        print("Telegram Received:", update.message.text)
        bot.send_message(chat_id=update.message.chat_id, text="Thank you for your input!")

    def collect(self, duration=None):
        # Source: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-–-Your-first-Bot
        self.inputs = []
        self.updater.start_polling()
        print("Running Telegram Bot")
        time.sleep(duration)
        self.updater.stop()

    @property
    def collected_inputs(self):
        return iter(self.inputs)
