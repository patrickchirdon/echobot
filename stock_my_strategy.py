import logging
import random
from datetime import timedelta

from lumibot.data_sources import AlpacaData
from lumibot.strategies.strategy import Strategy

"""
Strategy Description

This is meant to be a template to begin building strategies from. It will simply buy 
10 shares of `buy_symbol` the first day, sell them all the second day, 
buy 10 shares the next day, then sell them all on the fourth day, etc.
"""


class MyStrategy(Strategy):
    # =====Overloading lifecycle methods=============

    def initialize(self, buy_symbol="AGG"):
        # Set the initial variables or constants

        # Built in Variables
        self.sleeptime = 1

        # Our Own Variables
        self.counter = 0
        self.buy_symbol = buy_symbol

    def on_trading_iteration(self):
        # What to do each iteration
        all_positions = self.get_tracked_positions()
        if len(all_positions) > 0:
            for position in all_positions:
                selling_order = self.create_order(
                    self.buy_symbol, position.quantity, "sell"
                )
                self.submit_order(selling_order)

        # We can also do this to sell all our positions:
        # self.sell_all()

        if self.counter % 2 == 0:
            purchase_order = self.create_order(self.buy_symbol, 10, "buy")
            self.submit_order(purchase_order)

        self.counter = self.counter + 1

        # Wait until the end of the day
        self.await_market_to_close()

    def on_abrupt_closing(self):
        self.sell_all()

    def trace_stats(self, context, snapshot_before):
        random_number = random.randint(0, 100)
        row = {"my_custom_stat": random_number, "counter": self.counter}

        return row
