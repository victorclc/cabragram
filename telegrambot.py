from telegram.ext import Updater, CommandHandler
from telegram.chataction import ChatAction
from binance.client import Client
import common.helper as helper
import subprocess
import numpy as np
import querys
from matplotlib import pyplot as plt
import telegram

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
        self.client = Client(None, None)
        config = helper.load_config('datasource.cfg')
        DataManager.host = config['host']
        DataManager.db = config['database']
        DataManager.user = config['user']
        DataManager.pw = config['password']
        DataManager.prefix = config['table_prefix']
        DataManager.init_connector(config['connector'])

    def run(self):
        self.updater.start_polling()

    def init_handlers(self):
        start_handler = CommandHandler('start', self.start)
        profits_handler = CommandHandler('profits', self.total_profits)
        runchart_handler = CommandHandler('runchart', self.runchart)
        profitpercoin_handler = CommandHandler('profitpercoin', self.profitpercoin)
        opchart_handler = CommandHandler('opchart', self.opchart, pass_args=True)
        cycles_handler = CommandHandler('cycles', self.cycles)
        overview_handler = CommandHandler('overview', self.overview)
        details_handler = CommandHandler('details', self.details)
        price_variation_handler = CommandHandler('pricevar', self.opchart, pass_args=True)

        self.dispatcher.add_handler(start_handler)
        self.dispatcher.add_handler(profits_handler)
        self.dispatcher.add_handler(runchart_handler)
        self.dispatcher.add_handler(profitpercoin_handler)
        self.dispatcher.add_handler(opchart_handler)
        self.dispatcher.add_handler(cycles_handler)
        self.dispatcher.add_handler(overview_handler)
        self.dispatcher.add_handler(details_handler)
        self.dispatcher.add_handler(price_variation_handler)

    @staticmethod
    def start(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="AHHHHHHHHHHHHH")
        chat = update.message.chat
        user = TelegramPushUsers(chat.id, chat.first_name, chat.last_name, False)
        DataManager.persist(user)

    @staticmethod
    def total_profits(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        end_amount = DataManager.execute_query(
            "SELECT sum(end_amount) FROM c_instance WHERE run_id = ({})".format(querys.LAST_RUN_ID))[0]['sum']
        start_amount = DataManager.execute_query(
            "SELECT sum(start_amount) FROM c_instance WHERE run_id = ({})".format(querys.LAST_RUN_ID))[0]['sum']
        profit = (end_amount - start_amount) * 100 / start_amount
        bot.send_message(chat_id=update.message.chat_id, text="Profit: %.8f (%.2f%%)" % ((end_amount - start_amount),
                                                                                         profit))

    @classmethod
    def notify_push_users(cls, text):
        resp = DataManager.execute_query("SELECT chat_id FROM c_telegram_push_users WHERE send_push=true")
        for user in resp:
            cls.updater.bot.send_message(chat_id=user['chat_id'], text=text)

    @staticmethod
    def runchart(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        run_id = DataManager.execute_query(querys.LAST_RUN_ID)[0]
        start_amount = DataManager.execute_query(
            "SELECT sum(start_amount) FROM c_instance WHERE run_id = ({})".format(querys.LAST_RUN_ID))[0]['sum']
        cycles = DataManager.execute_query(
            "SELECT * FROM c_cycle WHERE status = 'COMPLETED' and run_id = ({}) ORDER BY ref_date".format(
                querys.LAST_RUN_ID))

        time = [cycle['ref_date'] for cycle in cycles]
        profits = []

        amount = start_amount
        for cycle in cycles:
            profits.append(amount + cycle['profit'])
            amount = amount + cycle['profit']

        plt.plot(time, profits)
        plt.title('Run (run_id={})'.format(run_id['run_id']))
        plt.savefig('tmp/runchart.png', bbox_inches='tight')

        with open("./tmp/runchart.png", 'rb') as file:
            bot.send_photo(chat_id=update.message.chat_id, photo=file)

        plt.close()

    @staticmethod
    def profitpercoin(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        operations = DataManager.execute_query(
            "SELECT * FROM c_instance WHERE run_id = ({})".format(querys.LAST_RUN_ID))

        msg = ""
        for op in operations:
            end_amount = op['end_amount']
            start_amount = op['start_amount']
            profit = op['perc']
            msg += "%s: %.8f (%.2f%%)\n" % (op['symbol'], (end_amount - start_amount), profit)

        bot.send_message(chat_id=update.message.chat_id, text=msg)

    @staticmethod
    def opchart(bot, update, args):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
        symbol = args[0]
        run_id = DataManager.execute_query(querys.LAST_RUN_ID)[0]['run_id']

        query = "SELECT * FROM c_analysis WHERE run_id=({}) AND symbol='{}'".format(querys.LAST_RUN_ID, symbol)

        res = DataManager.execute_query(query)

        price = [d['price'] for d in res if d['type'] == 'CHART']
        time = [d['ref_date'] for d in res if d['type'] == 'CHART']
        orders = [d['order_id'] for d in res if d['order_id']]

        plt.plot(time, price)

        txt = ''
        for order in orders:
            txt += '{},'.format(order)
        else:
            txt = txt[:-1]

        query = 'SELECT type, avg_price, ref_date from c_order where exec_amount > 0 and order_id in ({})'.format(txt)
        results = DataManager.execute_query(query)

        buy_price = []
        buy_time = []
        sell_price = []
        sell_time = []

        for result in results:
            if result['type'] == 'BUY':
                buy_price.append(result['avg_price'])
                buy_time.append(result['ref_date'])
            else:
                sell_price.append(result['avg_price'])
                sell_time.append(result['ref_date'])

        plt.plot(buy_time, buy_price, '^', markersize=5)
        plt.plot(sell_time, sell_price, 'v', markersize=5)

        plt.title("{} (run_id={})".format(symbol, run_id))
        plt.savefig('tmp/opchart.png', bbox_inches='tight')

        with open("./tmp/opchart.png", 'rb') as file:
            bot.send_photo(chat_id=update.message.chat_id, photo=file)

        plt.close()

    def cycles(self, bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        orders = DataManager.execute_query(querys.ACTIVE_CYCLES_BUY_ORDERS)
        msg = ""
        for order in orders:
            last_price = np.float64(self.client.get_ticker(symbol=order['symbol'])['lastPrice'])
            price = np.float64(order['price'])
            msg += "%s (%.2f%%)\n" % (order['symbol'], (last_price - price) * 100 / price)

        if msg:
            bot.send_message(chat_id=update.message.chat_id, text=msg)
        else:
            bot.send_message(chat_id=update.message.chat_id, text="0 'ACTIVE' cycles.")

    @staticmethod
    def overview(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        data = DataManager.execute_query(querys.RUN_OVERVIEW)[0]
        msg = "RUN OVERVIEW-------------------\n"

        for key, value in data.items():
            msg += "{}: {}\n".format(key, value)
        bot.send_message(chat_id=update.message.chat_id, text=msg)

    @staticmethod
    def details(bot, update):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        lines = DataManager.execute_query(querys.RUN_DETAILS)
        msg = ""

        for line in lines:
            msg += "{} DETAILS -------------------\n".format(line['symbol'])
            for key, value in line.items():
                msg += "{}: {}\n".format(key, value)
            msg += "\n"
        bot.send_message(chat_id=update.message.chat_id, text=msg)

    def price_variation(self, bot, update, args):
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
        cycle_id = args[0]


if __name__ == "__main__":
    bot = TelegramBot()
    bot.init_handlers()
    bot.run()
