from datetime import datetime

from credentials import ALPACA_CONFIG
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

"""
Strategy Description

This is meant to be a template to begin building strategies from. It will buy 
10 shares of `buy_symbol` every day.
"""


class BlankStrategy(Strategy):
    # =====Overloading lifecycle methods=============
    parameters = {"buy_symbol": "SPY"}

    def initialize(self):
        # There is only one trading operation per day
        # No need to sleep between iterations
        self.sleeptime = "1D"

        ##########################################
        # Example (you can delete this):
        ##########################################
        self.did_buy = False
        self.counter = 0
        ##########################################

    def on_trading_iteration(self):
        ## Write your code here

        ##########################################
        # Example (you can delete this):
        ##########################################
        buy_symbol = self.parameters["buy_symbol"]

        current_value = self.get_last_price(buy_symbol)
        if self.did_buy == False:
            if current_value > 0:
                order = self.create_order(buy_symbol, 10, "buy")
                self.submit_order(order)
                self.did_buy = True

        ##########################################


if __name__ == "__main__":
    is_live = False

    if is_live:
        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG)
        strategy = BlankStrategy(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Choose the time from and to which you want to backtest
        backtesting_start = datetime(2012, 1, 1)
        backtesting_end = datetime(2023, 1, 1)

        # Initialize the backtesting object
        print("Starting Backtest...")
        BlankStrategy.backtest(
            YahooDataBacktesting, backtesting_start, backtesting_end, parameters={}
        )
