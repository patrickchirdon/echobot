import os
import alpaca_trade_api as tradeapi
import time
from datetime import datetime, timedelta

# Set Alpaca API key and secret
API_KEY = 'keyhere'
API_SECRET = 'secret'
BASE_URL = 'https://api.alpaca.markets'

import os
import alpaca_trade_api as tradeapi
import time
from datetime import datetime, timedelta

# Create Alpaca API instance
api = tradeapi.REST(API_KEY, API_SECRET, base_url=BASE_URL)

# Define function to find all stocks on the NYSE priced below $5 and sort by highest average volume
def find_stocks():
    # Get all assets
    assets = api.list_assets(status='active')
    
    # Filter assets based on criteria
    stock_list = []
    for stock in assets:
        if stock.exchange == 'NYSE' and stock.tradable and stock.symbol.isalpha():
            # Get latest trade information
            trade = api.get_latest_trade(stock.symbol)
            if trade.price is not None and trade.price < 5:
                # With this line
             
                stock_data = api.get_bars(stock.symbol, timeframe='1D', limit=2).df
              
                # Check if the key 'HTY' exists in the DataFrame before accessing it
                if stock.symbol in stock_data.index:
                    stock.avg_volume = stock_data.loc[stock.symbol, 'volume'].mean()
                    print(stock.avg_volume)
                else:
                # Handle the case when the key does not exist in the DataFrame
                    print(f"Key '{stock.symbol}' not found in DataFrame")


                stock_list.append(stock)
                
                
    

# Sort the list based on average volumes in descending order
    stock_list.sort(key=lambda x: x.avg_volume if hasattr(x, 'avg_volume') else 0, reverse=True)
    stock_quote=stock_list[0]
    stock_quote1=stock_list[1]
    stock_quote2=stock_list[2]
    stock_quote3=stock_list[3]
    stock_quote4=stock_list[4]
    topfive=[stock_quote.symbol, stock_quote1.symbol, stock_quote2.symbol, stock_quote3.symbol, stock_quote4.symbol]
    
    #select the best stock
    print(stock_list)
    print(stock_quote.symbol)
    print(topfive)
    
    
    return stock_list, stock_quote, topfive

# Define function to buy stocks
def buy_stock(stock, cash):
    stock_quote = api.get_latest_trade(stock)
    qty = int(float(cash) // float(stock_quote.price))
    api.submit_order(
        symbol=stock,
        qty=qty,
        side='buy',
        type='market',
        time_in_force='gtc'
    )
    print(f"Buy {stock}: {qty} shares at ${stock_quote.price:.2f}")
    return qty

# Define function to sell stocks with 5% return
def sell_stock(stock):
    stock_bars = api.get_barset(stock, 'day', limit=2).df[stock]
    stock_return = (stock_bars['close'][-1] / stock_bars['close'][0]) - 1
    if stock_return >= 0.05:
        stock_quote = api.get_latest_trade(stock)
        
        position = api.get_position(stock)
        api.submit_order(
            symbol=stock,
            qty=position.qty,
            side='sell',
            type='market',
            time_in_force='gtc'
        )
        print(f"Sell {stock}: {position.qty} shares at ${stock_quote:.2f}")

# Define function to check if market is closed
def is_market_closed():
    clock = api.get_clock()
    return clock.is_open

# Define function to print returns
def print_returns():
    # Get the current portfolio
    portfolio = api.list_positions()
    total_returns = 0
    for position in portfolio:
        stock_symbol = position.symbol
        stock_bars = api.get_barset(stock_symbol, 'day', limit=2).df[stock_symbol]
        stock_return = (stock_bars['close'][-1] / stock_bars['close'][-2]) - 1
        total_returns += stock_return
    print(f"Total Returns: {total_returns * 100:.2f}%")

# Main loop
while True:
    # Check if market is closed
    
    
    # Find and print stocks priced below $5 on NYSE sorted by highest average volume
    stock_list, stock_quote, topfive = find_stocks()
    print("Stocks priced below $5 on NYSE sorted by highest average volume:")
    print(stock_list)
    print('the top penny stock is')
    print(str(stock_quote))
    print('the symbol is')
    print(str(stock_quote.symbol))
    print('The top five stocks are')
    print(str(topfive))
    
    # Select stock with highest average volume
    if len(stock_list) > 0:
        stock = stock_list[0]

        # Buy stock with highest volume
        cash = api.get_account().cash
        mytrade = api.get_latest_trade(stock.symbol).price
        
        if float(cash) > mytrade:
            buy_stock(stock.symbol, cash)
            time.sleep(60)
            sell_stock(stock.symbol)
            print_returns()
        else:
            print("Insufficient funds.")
            time.sleep(60)
    else:
        print("No stocks found.")
        time.sleep(60)
