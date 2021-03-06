import requests
import re
import sys
import json
from threading import Thread, Timer
from datetime import datetime
import time


def usd_to_brl():
    url = "http://free.currencyconverterapi.com/api/v5/convert?q=USD_BRL&compact=y"
    response = requests.request("GET", url)
    ticker = json.loads(response.text)
    return float(ticker['USD_BRL']['val'])


class Exchange:

    def __init__(self, coin):
        self.coin = coin
        self.headers = {'content-type': 'application/json'}
        self.url_ticker = ""
        self.url_orders = ""
        self.response = ""
        self.ticker = ""
        self.fee = 0.005 # 0.5%
        self.asks = [None]
        self.bids = [None]

    def __str__(self):
        return self.__class__.__name__ + '_' + self.coin

    def nickname(self):
        return (self.__class__.__name__[:6] + '_' + self.coin).upper()

    #coin = 'btc' or 'ltc'
    def get_ticker(self):
        self.response = requests.request("GET", self.url_ticker, headers=self.headers)
        self.ticker = json.loads(self.response.text)
        return self.ticker

    def print_ticker(self):
        print(json.dumps(self.ticker, indent=4, sort_keys=True))

    def print_ticker_prices(self):
        print(("{0:.2f}".format(self.buy())), ' ', ("{0:.2f}".format(self.sell())), ' ', ("{0:.2f}".format(self.last())),
              ' ', self.nickname())

    def buy(self):
        #return json.loads(self.response.text)['buy']
        return float(self.ticker['buy'])

    def sell(self):
        #return json.loads(self.response.text)['sell']
        return float(self.ticker['sell'])

    def last(self):
        return float(self.ticker['last'])

    def get_orders(self):
        self.response = requests.request("GET", self.url_orders, headers=self.headers)
        self.asks = json.loads(self.response.text)['asks']
        self.bids = json.loads(self.response.text)['bids']

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
        Exchange.__init__(self, coin.upper())
        self.url_ticker = "https://www.mercadobitcoin.net/api/%s/ticker/" % self.coin
        self.url_orders = "https://www.mercadobitcoin.net/api/%s/orderbook" % self.coin
        self.fee = 0.007  # 0.7%

    def buy(self):
        return float(self.ticker['ticker']['buy'])

    def sell(self):
        return float(self.ticker['ticker']['sell'])

    def last(self):
        return float(self.ticker['ticker']['last'])


class NegocieCoins(Exchange):
    def __init__(self, coin):
        Exchange.__init__(self, coin.lower())
        self.url_ticker = "https://broker.negociecoins.com.br/api/v3/%sbrl/ticker" % self.coin
        self.url_orders = "https://broker.negociecoins.com.br/api/v3/%sbrl/orderbook" % self.coin
        self.fee = 0.004  # 0.4%

    def get_orders(self):
        self.response = requests.request("GET", self.url_orders, headers=self.headers)
        self.asks = json.loads(self.response.text)['ask']
        self.bids = json.loads(self.response.text)['bid']


    def ask(self, index):
        return [self.asks[index]['price'], self.bids[index]['quantity']]

    def bid(self, index):
        return [self.bids[index]['price'], self.bids[index]['quantity']]


class FlowBTC(Exchange):
    def __init__(self, coin):
        Exchange.__init__(self, coin.upper())
        self.url_ticker = "https://api.flowbtc.com:8400/GetTicker/BTCBRL/"
        #self.url_ticker = "https://trader.flowbtc.com/ajax/v1/GetTicker/"
        #self.url_ticker = "https://api.flowbtc.com:8400/ajax/v1/GetTicker/"
        self.url_orders = "https://api.flowbtc.com:8400/GetOrderBook/BTCBRL/"
        self.fee = 0.0035  # 0.35%

    def get_ticker(self):
        parameters = (('productPair', 'BTCBRL'))
        self.response = requests.request("POST", self.url_ticker, headers=self.headers)
        print(self.response)
        #self.ticker = json.loads(self.response.text)
        return self.ticker

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


class Braziliex(Exchange):
    def __init__(self, coin):
        Exchange.__init__(self, coin.lower())
        self.url_ticker = "https://braziliex.com/api/v1/public/ticker/%s_brl" % self.coin
        self.url_orders = "https://braziliex.com/api/v1/public/orderbook/%s_brl" % self.coin
        self.fee = 0.005  # 0.5%

    def get_orders(self):
        self.response = requests.request("GET", self.url_orders, headers=self.headers)
        self.asks = json.loads(self.response.text)['asks']
        self.bids = json.loads(self.response.text)['bids']

    def buy(self):
        return float(self.ticker['lowestAsk'])

    def sell(self):
        return float(self.ticker['highestBid'])

    def ask(self, index):
        return [self.asks[index]['price'], self.bids[index]['amount']]

    def bid(self, index):
        return [self.bids[index]['price'], self.bids[index]['amount']]


class FoxBit(Exchange):
    def __init__(self, coin):
        Exchange.__init__(self, coin.upper())
        self.url_ticker = "https://api.blinktrade.com/api/v1/BRL/ticker?crypto_currency=%s" % self.coin
        self.url_orders = "https://api.blinktrade.com/api/v1/BRL/orderbook?crypto_currency=%s" % self.coin
        self.fee = 0.005  # 0.5%

    def get_orders(self):
        self.response = requests.request("GET", self.url_orders, headers=self.headers)
        self.asks = json.loads(self.response.text)['asks']
        self.bids = json.loads(self.response.text)['bids']



class BitcoinTrade(Exchange):
    def __init__(self, coin):
        Exchange.__init__(self, coin.upper())
        self.url_ticker = "https://api.bitcointrade.com.br/v1/public/%s/ticker" % self.coin
        self.url_orders = "https://api.bitcointrade.com.br/v1/public/%s/orders" % self.coin
        self.fee = 0.005  # 0.5%

    def get_orders(self):
        self.response = requests.request("GET", self.url_orders, headers=self.headers)
        self.asks = json.loads(self.response.text)['data']['asks']
        self.bids = json.loads(self.response.text)['data']['bids']

    def buy(self):
        return float(self.ticker['data']['buy'])

    def sell(self):
        return float(self.ticker['data']['sell'])

    def last(self):
        return float(self.ticker['data']['last'])

    def ask(self, index):
        return [self.asks[index]['unit_price'], self.bids[index]['amount']]

    def bid(self, index):
        return [self.bids[index]['unit_price'], self.bids[index]['amount']]



class Bitfinex(Exchange):
    def __init__(self, coin):
        Exchange.__init__(self, coin.upper())
        self.url_ticker = "https://api.bitfinex.com/v2/ticker/t%sUSD" % self.coin
        self.url_orders = "https://api.bitfinex.com/v2/tickers?symbols=t%sUSD" % self.coin
        self.fee = 0.005  # 0.5%

    def get_ticker(self):
        self.response = requests.request("GET", self.url_ticker, headers=self.headers)
        self.ticker = self.response.text[1:-1].split(',')
        return self.ticker

    def get_orders(self):
        self.response = ""
        # do nothing

    def buy(self):
        return float(self.ticker[0]) * usd_to_brl()

    def sell(self):
        return float(self.ticker[2]) * usd_to_brl()

    def last(self):
        return float(self.ticker[6]) * usd_to_brl()

    def ask(self, index):
        return self.sell()

    def bid(self, index):
        return self.buy()



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

def run_arbitrage_verification(interval_sec, total_time_sec):
    # it auto-starts, no need of rt.start()
    rt = RepeatedTimer(interval, check_opportunity_thread)
    try:
        # your long-running job goes here...
        time.sleep(total_time)
    finally:
        # better in a try/finally block to make sure the program ends!
        rt.stop


def request_prices_btc():
    exchanges_btc = [Bitfinex('BTC'), BitcoinTrade('BTC'), Braziliex('btc'), MercadoBitcoin('BTC'), NegocieCoins('btc'), FoxBit('BTC'), ]
    for ex in exchanges_btc:
        try:
            ex.get_ticker()
            ex.print_ticker_prices()
        except:
            print("Unexpected error trying to connect ", ex)


def request_prices_bch():
    exchanges_btc = [ BitcoinTrade('BCH'), Braziliex('bch'), MercadoBitcoin('BCH'), NegocieCoins('bch')]
    for ex in exchanges_btc:
        try:
            ex.get_ticker()
            ex.print_ticker_prices()
        except:
            print("Unexpected error trying to connect ", ex)


def request_prices_ltc():
    exchanges_btc = [ Bitfinex('LTC'), BitcoinTrade('LTC'), Braziliex('ltc'), MercadoBitcoin('LTC'), NegocieCoins('ltc')]
    for ex in exchanges_btc:
        try:
            ex.get_ticker()
            ex.print_ticker_prices()
        except:
            print("Unexpected error trying to connect ", ex)


def coin_to_file(filename, coin):
    with open(filename, "a+") as btc_file:
        exchanges_btc = [Bitfinex(coin), BitcoinTrade(coin), Braziliex(coin), MercadoBitcoin(coin), NegocieCoins(coin), FoxBit(coin)]
        btc_file.write(time.strftime("\n%Y%m%d-%H%M%S "))
        print(time.strftime("\n%Y%m%d-%H%M%S "))
        for ex in exchanges_btc:
            try:
                ex.get_ticker()
                btc_file.write(
                    ex.nickname() + ' ' + ("{0:.2f}".format(ex.buy())) + ' ' + ("{0:.2f}".format(ex.sell())) + ' ' + (
                        "{0:.2f}".format(ex.last())) + ' ')
                print(
                    ex.nickname() + ' ' + ("{0:.2f}".format(ex.buy())) + ' ' + ("{0:.2f}".format(ex.sell())) + ' ' + (
                        "{0:.2f}".format(ex.last())) + ' ')

            except:
                print("Unexpected error trying to connect ", ex)





if __name__ == "__main__" :

    #interval = 60 # seconds
    #total_time = 60 * 60 * 9   # 9 hours

    #interval = 2 # seconds
    #total_time = 5
    #run_arbitrage_verification(interval, total_time)


    print('------------ BTC - <buy, sell, last>')
    request_prices_btc()
    print('------------ BCH - <buy, sell, last>')
    request_prices_bch()
    print('------------ LTC - <buy, sell, last>')
    request_prices_ltc()

    period = 5 * 60 # in seconds

    print('------------ BTC - To File <buy, sell, last>')
    while(True):
        coin_to_file("btc_prices.txt", 'btc')
        time.sleep(period)

    print('------------ BCH - To File <buy, sell, last>')
    while (True):
        coin_to_file("bch_prices.txt", 'bch')
        time.sleep(period)

    print('------------ LTC - To File <buy, sell, last>')
    while (True):
        coin_to_file("ltc_prices.txt", 'ltc')
        time.sleep(period)

    #usd = usd_to_brl()
    #print(usd)



    input("\nPress [Enter] to continue...")

