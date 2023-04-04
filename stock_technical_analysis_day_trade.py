import logging
import time
from datetime import datetime, timedelta

import ta
from lumibot.strategies.strategy import Strategy

"""
Strategy Description 

This strategy will use the RSI indicator to determine the balance of 
assets in the postfolio, essentially "buying low" and "selling high".

In a normal situation it will divide its money between `main_symbol` 
and `other_symbol`, based on `middle_main_symbol_percentage`.
In an UPPER situation (when we hit the `upper_threshold` for RSI), we will only 
own `other_symbol` and sell all of our `main_symbol`.
In a LOWER situation (when we hit the `lower_threshold` for RSI), we will only
own `main_symbol` and sell all of our `other_symbol`.
"""


class STATES:
    UPPER = "UPPER"
    LOWER = "LOWER"
    MIDDLE = "MIDDLE"


class TechnicalAnalysis(Strategy):
    # =====Overloading lifecycle methods=============

    def initialize(
        self,
        main_symbol="SPY",
        other_symbol="TLT",
        lower_threshold=33,
        upper_threshold=66,
        middle_main_symbol_percentage=0.6,
    ):
        # There is only one trading operation per day
        # No need to sleep between iterations
        self.sleeptime = 1

        self.main_symbol = main_symbol
        self.other_symbol = other_symbol
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.middle_main_symbol_percentage = middle_main_symbol_percentage

        self.current_state = None

    def on_trading_iteration(self):
        symbol = self.main_symbol
        current_rsi = self.get_rsi(symbol)
        current_position = self.get_tracked_position(symbol)

        # Only buy our main symbol
        if current_rsi < self.lower_threshold and self.current_state != STATES.LOWER:
            self.sell_all()

            # Only buy the main symbol
            current_price = self.get_last_price(self.main_symbol)
            quantity = self.portfolio_value // current_price
            order = self.create_order(self.main_symbol, quantity, "buy")
            # If I wantd to do a trailing stop I would do this:
            # order = self.create_order(self.main_symbol, quantity, "buy", trail_percent=2.0)
            self.submit_order(order)

        # Only buy our other symbol
        elif current_rsi > self.upper_threshold and self.current_state != STATES.UPPER:
            self.sell_all()

            # Only buy the other symbol
            current_price = self.get_last_price(self.other_symbol)
            quantity = self.portfolio_value // current_price
            order = self.create_order(self.other_symbol, quantity, "buy")
            self.submit_order(order)

        # Buy a mix of main and other symbol in the proportion determined
        # by self.middle_main_symbol_percentage
        elif self.current_state != STATES.MIDDLE:
            self.sell_all()

            # Buy main symbol
            main_current_price = self.get_last_price(self.main_symbol)
            main_amount_to_buy = (
                self.portfolio_value * self.middle_main_symbol_percentage
            )
            main_quantity = main_amount_to_buy // main_current_price
            order = self.create_order(self.main_symbol, main_quantity, "buy")
            self.submit_order(order)

            # Buy other symbol
            other_current_price = self.get_last_price(self.other_symbol)
            other_amount_to_buy = self.portfolio_value * (
                1 - self.middle_main_symbol_percentage
            )
            other_quantity = other_amount_to_buy // other_current_price
            order = self.create_order(self.other_symbol, other_quantity, "buy")
            self.submit_order(order)

    def on_abrupt_closing(self):
        # Sell all positions when you hit ctrl + C
        self.sell_all()

    # =============Helper methods====================

    def get_rsi(self, symbol, period=14):
        bars_set = self.get_symbol_bars(symbol, period, "minute")
        rsi = ta.momentum.rsi(bars_set.df["close"])[-1]
        return rsi
