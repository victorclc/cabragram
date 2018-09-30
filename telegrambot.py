from telegram.ext import Updater, CommandHandler
from telegram.chataction import ChatAction
from binance.client import Client
from common.utils import just_a_logger, load_config
import subprocess
import numpy as np

from database.datamanager import DataManager


class TelegramPushUsers(object):
    def __init__(self, chat_id, first_name, last_name, send_push):
        self.chat_id = chat_id
        self.first_name = first_name
        self.last_name = last_name
        self.send_push = send_push

    def persistables(self):
        pers = {
            'chat_id': self.chat_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'send_push': self.send_push,
            '__key__': 'chat_id'
        }
        return pers


class TelegramBot(object):
    """
    A telegram bot for push notification and stuff
    """
    # logger = just_a_logger('CabratraderBot')
    updater = Updater(token='615223894:AAHWsjntxCsnn9SFPhAKmP3CC-wVeRlA-8U')
    dispatcher = updater.dispatcher

    def __init__(self):
        bin_cfg = load_config('cfg/binance.cfg')['keys'][0]
        self.client = Client(bin_cfg['key'], bin_cfg['secret'])

    def run(self):
        self.updater.start_polling()

    def init_handlers(self):
        help_handler = CommandHandler('help', self.help)
        start_handler = CommandHandler('start', self.start)
        status_handler = CommandHandler('status', self.status)
        torros_handler = CommandHandler('torros', self.torros)
        hino_handler = CommandHandler('hino', self.hino)
        meavisa_handler = CommandHandler('meavisadosciclosai', self.meavisadosciclosai)
        paradeavisar_handler = CommandHandler('parademeavisarporra', self.parademeavisarporra)
        profits_handler = CommandHandler('profits', self.total_profits)

        self.dispatcher.add_handler(help_handler)
        self.dispatcher.add_handler(start_handler)
        self.dispatcher.add_handler(status_handler)
        self.dispatcher.add_handler(torros_handler)
        self.dispatcher.add_handler(hino_handler)
        self.dispatcher.add_handler(meavisa_handler)
        self.dispatcher.add_handler(paradeavisar_handler)
        self.dispatcher.add_handler(profits_handler)

    @staticmethod
    def help(bot, update):
        text = "/start AHHHHHHHHHHHHH\n/" + \
               "status Status da cabra\n" + \
               "/hino  Hino da cabra\n" + \
               "/torros Balances retornado pela exchange\n" + \
               "/profits Total profits da ultima run\n" + \
               "/meavisadosciclosai Se registra para receber info dos ciclos\n" + \
               "/parademeavisarporra Se des-registra para receber info dos ciclos"

        bot.send_message(chat_id=update.message.chat_id, text=text)

    @staticmethod
    def start(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="AHHHHHHHHHHHHH")

    @staticmethod
    def status(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        process = subprocess.Popen("./integrations/telegram/scripts/checkCabra.sh", stdout=subprocess.PIPE)
        process.communicate()

        if process.returncode == 1:
            with open("./integrations/telegram/assets/dormindo.jpg", 'rb') as file:
                bot.send_photo(chat_id=update.message.chat_id, photo=file)
        else:
            with open("./integrations/telegram/assets/rodando.gif", 'rb') as file:
                bot.send_document(chat_id=update.message.chat_id, document=file)

    @staticmethod
    def hino(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="https://www.youtube.com/watch?v=oTDVRT6rDzE")

    def torros(self, bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        ret = self.client.get_account()
        text = ""
        for balance in ret['balances']:
            asset = balance['asset']
            amount = np.float64(balance['free']) + np.float64(balance['locked'])

            if amount > 0.0:
                text += '%s: %.8f\n' % (asset, amount.round(8))

        bot.send_message(chat_id=update.message.chat_id, text=text)

    @staticmethod
    def meavisadosciclosai(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        chat = update.message.chat
        user = TelegramPushUsers(chat.id, chat.first_name, chat.last_name, True)
        DataManager.persist(user)
        bot.send_message(chat_id=chat.id, text="OK!")

    @staticmethod
    def parademeavisarporra(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        chat = update.message.chat
        user = TelegramPushUsers(chat.id, chat.first_name, chat.last_name, False)
        DataManager.persist(user)
        bot.send_message(chat_id=chat.id, text="Nao vou te mandar mais nada então fdp!")

    @staticmethod
    def total_profits(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        resp = DataManager.execute_query(
            "SELECT sum(profit) from c_cycle where status='COMPLETED' and run_id = (select run_id from c_run order by run_id desc limit 1)")[0]
        profit = float(resp['sum']) * 100 / 0.1
        bot.send_message(chat_id=update.message.chat_id, text="Profit: %.8f (%.2f%%)" % (float(resp['sum']), profit))

    @classmethod
    def notify_push_users(cls, text):
        resp = DataManager.execute_query("SELECT chat_id FROM c_telegram_push_users WHERE send_push=true")
        for user in resp:
            cls.updater.bot.send_message(chat_id=user['chat_id'], text=text)
