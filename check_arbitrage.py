import requests
import re
import sys
import json
from threading import Thread, Timer
from datetime import datetime
import time



class Exchange:

    def __init__(self, coin):
        self.coin = coin
        self.headers = {'content-type': 'application/json'}
        self.url_ticker = ""
        self.url_orders = ""
        self.response = ""
        self.ticker = ""
        self.fee = 0.5 * 0.01 # percent of the operation
        self.asks = [None]
        self.bids = [None]

    def __str__(self):
        return self.__class__.__name__ + '_' + self.coin

    #coin = 'btc' or 'ltc'
    def get_ticker(self):
        self.response = requests.request("GET", self.url_ticker, headers=self.headers)
        self.ticker = json.loads(self.response.text)
        #print(json.dumps(self.ticker, indent=4, sort_keys=True))

    def buy(self):
        #return json.loads(self.response.text)['buy']
        return float(self.ticker['buy'])

    def sell(self):
        #return json.loads(self.response.text)['sell']
        return float(self.ticker['sell'])

    def get_orders(self):
        self.response = requests.request("GET", self.url_orders, headers=self.headers)
        self.asks = json.loads(self.response.text)['asks']
        self.bids = json.loads(self.response.text)['bids']

        # print (response.text)
        #data = json.loads(self.response.text)
        # print(json.dumps(data, indent=4, sort_keys=True))

        #asks = data['asks']
        #bids = data['bids']

        #with open('mercadobitcoin_orderbook_%s.json' % coin, 'w') as outfile:
        #    json.dump(data, outfile, indent=4, sort_keys=True)

    def ask(self, index):
        return self.asks[index]

    def bid(self, index):
        return self.asks[index]



    def save_asks_file(self):
        filename = self.__class__.__name__ + '_' + self.coin + '_asks.json'
        print (filename)
        with open(filename, 'w') as outfile:
            json.dump(self.asks, outfile, indent=4, sort_keys=True)

    def save_bids_file(self):
        filename = self.__class__.__name__ + '_' + self.coin + '_bids.json'
        print (filename)
        with open(filename, 'w') as outfile:
            json.dump(self.bids, outfile, indent=4, sort_keys=True)



class MercadoBitcoin(Exchange):
    def __init__(self, coin):
        Exchange.__init__(self, coin)
        self.url_ticker = "https://www.mercadobitcoin.net/api/%s/ticker/" % coin
        self.url_orders = "https://www.mercadobitcoin.net/api/%s/orderbook" % coin
        self.fee = 0.7  # percent of the operation

    def buy(self):
        return float(self.ticker['ticker']['buy'])

    def sell(self):
        return float(self.ticker['ticker']['sell'])



class NegocieCoins(Exchange):
    def __init__(self, coin):
        Exchange.__init__(self, coin)
        self.url_ticker = "https://broker.negociecoins.com.br/api/v3/%sbrl/ticker" % coin
        self.url_orders = "https://broker.negociecoins.com.br/api/v3/%sbrl/orderbook" % coin
        self.fee = 0.4  # percent of the operation

    def get_orders(self):
        self.response = requests.request("GET", self.url_orders, headers=self.headers)
        self.asks = json.loads(self.response.text)['ask']
        self.bids = json.loads(self.response.text)['bid']


    def ask(self, index):
        return [self.asks[index]['price'], self.bids[index]['quantity']]

    def bid(self, index):
        return [self.bids[index]['price'], self.bids[index]['quantity']]


class BitcoinTrade(Exchange):
    def __init__(self):
        Exchange.__init__(self, 'BTC')
        self.url_ticker = "https://api.bitcointrade.com.br/v1/public/BTC/ticker"
        self.url_orders = "https://api.bitcointrade.com.br/v1/public/BTC/orders"
        self.fee = 0.5  # percent of the operation

    def get_orders(self):
        self.response = requests.request("GET", self.url_orders, headers=self.headers)
        self.asks = json.loads(self.response.text)['data']['asks']
        self.bids = json.loads(self.response.text)['data']['bids']

    def buy(self):
        return float(self.ticker['data']['buy'])

    def sell(self):
        return float(self.ticker['data']['sell'])

    def ask(self, index):
        return [self.asks[index]['unit_price'], self.bids[index]['amount']]

    def bid(self, index):
        return [self.bids[index]['unit_price'], self.bids[index]['amount']]





class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False



def compute_arbitrage(ex_buy, ex_sell, buy, sell):
    buy_fee = buy * ex_sell.fee * 0.01
    sell_fee = sell * ex_buy.fee * 0.01
    buy_price = buy + buy_fee
    sell_price = sell - sell_fee
    profit = sell_price - buy_price

    if profit > 0:
        print("Lucro   : " + ("{0:.2f}".format(profit)))

        #filename = time.strftime("%Y%m%d-%H%M%S") + '.txt'
        #file = open(filename, 'w')
        print(time.strftime("%Y%m%d-%H%M%S") + '\n')
        print("Comprar " + ("{0:.2f}".format(sell)) + "  " + str(ex_sell))
        print("Vender  " + ("{0:.2f}".format(buy)) + "  " + str(ex_buy))
        print("Comprar " + ("{0:.2f}".format(sell)) + " + " + ("{0:.2f}".format(buy_fee)) + " = " + (
        "{0:.2f}".format(buy_price)))
        print("Vender  " + ("{0:.2f}".format(buy)) + " - " + ("{0:.2f}".format(sell_fee)) + " = " + (
        "{0:.2f}".format(sell_price)))
        print("Lucro  : " + ("{0:.2f}".format(profit)))
        #file.close()
    else:
        print("Prejuizo: " + ("{0:.2f}".format(profit)))

    return profit


def check_opportunity(exchanges):
    success = True
    for ex in exchanges:
        try:
            ex.get_ticker()
        except:
            print("Unexpected error trying to connect ", ex)
            success = False

    if success:
        for ex_buy in exchanges:
            for ex_sell in exchanges:
                buy = ex_buy.buy()
                sell = ex_sell.sell()
                if buy > sell:
                    compute_arbitrage(ex_buy, ex_sell, buy, sell)


def check_opportunity_thread():
    print('\n--> ', str(datetime.now()))
    exchanges_btc = [MercadoBitcoin('btc'), NegocieCoins('btc'), BitcoinTrade()]
    exchanges_ltc = [MercadoBitcoin('ltc'), NegocieCoins('ltc')]
    print('\n-- btc')
    check_opportunity(exchanges_btc)
    print('\n-- ltc')
    check_opportunity(exchanges_ltc)
    sys.stdout.flush()


if __name__ == "__main__" :

    interval = 60 # seconds
    total_time = 60 * 60 * 9

    # it auto-starts, no need of rt.start()
    rt = RepeatedTimer(interval, check_opportunity_thread)
    try:
        # your long-running job goes here...
        time.sleep(total_time)
    finally:
        # better in a try/finally block to make sure the program ends!
        rt.stop()

    print("exiting...")


