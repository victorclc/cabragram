from telegram.ext import Updater, CommandHandler
from telegram.chataction import ChatAction
# from binance.client import Client
import common.helper as helper
import subprocess
import numpy as np
import querys
from database.datamanager import DataManager
from matplotlib import pyplot as plt

config = helper.load_config('datasource.cfg')
DataManager.host = config['host']
DataManager.db = config['database']
DataManager.user = config['user']
DataManager.pw = config['password']
DataManager.prefix = config['table_prefix']
DataManager.init_connector(config['connector'])


def total_profits(update):
    end_amount = DataManager.execute_query(
        "SELECT sum(end_amount) FROM c_operation WHERE run_id = ({})".format(querys.LAST_RUN_ID))[0]['sum']
    start_amount = DataManager.execute_query(
        "SELECT sum(start_amount) FROM c_operation WHERE run_id = ({})".format(querys.LAST_RUN_ID))[0]['sum']
    profit = (end_amount - start_amount) * 100 / start_amount
    print("Profit: %.8f (%.2f%%)" % ((end_amount - start_amount), profit))


def runchart():
    run_id = DataManager.execute_query(querys.LAST_RUN_ID)[0]
    start_amount = DataManager.execute_query(
        "SELECT sum(start_amount) FROM c_operation WHERE run_id = ({})".format(querys.LAST_RUN_ID))[0]['sum']
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

runchart()
