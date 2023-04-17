import os, sys
import csv
import requests
import urllib.request
import time
import optparse
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
from datetime import date, datetime, timedelta
from pytz import timezone
from random import randint
from urllib.parse import urlparse


import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError

NASDAQ_API_URL = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=100&marketcap=large|mid|small&recommendation=strong_buy|buy"

STOCKBOT_VERSION = '0.1-b.3'
__version__ = STOCKBOT_VERSION

TZ = timezone('America/New_York')

APIKEYID = 'AKUE4RB5KZX72PI3WEZ4'
APISECRETKEY = 'dACLoD5fTFbioKs4Xf7aEfnzpYPKx9NDYx9yYRnU'
APIBASEURL = 'https://api.alpaca.markets'

api = tradeapi.REST(APIKEYID, APISECRETKEY, APIBASEURL)

stock_info = []

strong_buy_stocks = []


def get_stock_info(stock):
    n = randint(1,2)
    url = "https://query{}.finance.yahoo.com/v8/finance/chart/{}?region=US&lang=en-US&includePrePost=false&interval=1d&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance".format(n, stock)
    # stagger requests to avoid connection issues to yahoo finance
    time.sleep(randint(1, 3))
    headers = {
            'authority': 'query{}.finance.yahoo.com'.format(n),
            'method': 'GET',
            'scheme': 'https',
            'path': '/v8/finance/chart/{}?region=US&lang=en-US&includePrePost=false&interval=1d&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance'.format(stock),
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-laguage': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'sec-fetch-dest': 'document',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'sec-fetch-mode': 'navigate',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
            }
    try:
        r = requests.get(url, headers=headers)
    except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError) as e:
        print('CONNECTION ERROR: {}'.format(e))
        time.sleep(randint(2, 5))
        get_stock_info(stock)
    stock_ = r.json()
    if stock_data['chart']['result'] is None:
        return None
    return stock_data





def get_nasdaq_listed():
    nasdaqlist_url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt"
    nasdaqlist_file = "nasdaqlisted.txt"
    if os.path.exists(nasdaqlist_file):
        age_in_sec = time.time() - os.path.getmtime(nasdaqlist_file)
        if age_in_sec > 604800:  # 1 week
            os.remove(nasdaqlist_file)
            urllib.request.urlretrieve(nasdaqlist_url, nasdaqlist_file)
    else:
        urllib.request.urlretrieve(nasdaqlist_url, nasdaqlist_file)
    nyse_tickers = []
    with open(nasdaqlist_file, 'r') as csvfile:
        filereader = csv.reader(csvfile, delimiter='|', quotechar='"')
        for row in filereader:
            nyse_tickers.append(row[0])
    del nyse_tickers[0]
    del nyse_tickers[-1]
    return nyse_tickers


def get_nasdaq_buystocks():
    # api used by https://www.nasdaq.com/market-activity/stocks/screener
    url = NASDAQ_API_URL
    parsed_uri = urlparse(url)
    # stagger requests to avoid connection issues to nasdaq.com
    time.sleep(randint(1, 3))
    headers = {
        'authority': parsed_uri.netloc,
        'method': 'GET',
        'scheme': 'https',
        'path': parsed_uri.path + '?' + parsed_uri.params,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-laguage': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'sec-fetch-dest': 'document',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        }
    try:
        r = requests.get(url, headers=headers)
    except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError) as e:
        print('CONNECTION ERROR: {}'.format(e))
        time.sleep(randint(2, 5))
        get_nasdaq_buystocks()
    return r.json()
 
import json


hello=get_nasdaq_buystocks()

print(json.dumps(hello, indent=4))


