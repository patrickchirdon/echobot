from datetime import datetime, timedelta

import pandas as pd
import quandl
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

from credentials import AlpacaConfig

"""
Strategy Description

This strategy will buy a few symbols that have 2x or 3x returns (have leverage), but will 
also diversify and rebalance the portfolio often.
"""


class DiversifiedLeverageAdjust(Strategy):
    # =====Overloading lifecycle methods=============

    parameters = {
        "portfolio": [
            {
                "symbol": "TQQQ",  # 3x Leveraged Nasdaq
                "weight": 0.20,
            },
            {
                "symbol": "UPRO",  # 3x Leveraged S&P 500
                "weight": 0.10,
            },
            {
                "symbol": "UDOW",  # 3x Leveraged Dow Jones
                "weight": 0.10,
            },
            {
                "symbol": "EDC",  # 3x Leveraged Emerging Markets
                "weight": 0.10,
            },
            {
                "symbol": "TMF",  # 3x Leveraged Treasury Bonds
                "weight": 0.30,
            },
            {
                "symbol": "UGL",  # 3x Leveraged Gold
                "weight": 0.05,
            },
            {
                "symbol": "AGQ",  # 3x Leveraged Silver
                "weight": 0.05,
            },
            {
                "symbol": "VIXM",  # VIX ETF
                "weight": 0.10,
            },
        ],
        "rebalance_period": 4,
        "interest_rate": 2,
    }

    def initialize(self):

        # Setting the waiting period (in days) and the counter
        self.counter = 0

        # There is only one trading operation per day
        # no need to sleep between iterations
        self.sleeptime = "1D"

        # Initializing the portfolio variable with the assets and proportions we want to own
        self.initialized = False

        self.minutes_before_closing = 1
        self.last_updated = None

    def on_trading_iteration(self):
        rebalance_period = self.parameters["rebalance_period"]
        # If the target number of days (period) has passed, rebalance the portfolio
        if self.counter == rebalance_period or self.counter == 0:
            self.counter = 0

            # Adjust the portfolio weights
            dt = datetime.now()
            if self.last_updated is None or dt < self.last_updated - timedelta(hours=1):
                quandl.ApiConfig.api_key = "sZBNDY6CYyVfFSwAbmeY"
                self.df = quandl.get("FRED/DGS10")
                self.last_updated = dt
                self.df.index = pd.to_datetime(self.df.index).date

            curr_date = self.get_datetime().date()
            values = self.df.iloc[self.df.index == curr_date]["Value"].values
            if len(values) > 0:
                current_interest_rate = values[0]
            else:
                values = self.df.iloc[self.df.index <= curr_date]["Value"].values
                current_interest_rate = values[-1]
            self.log_message(
                f"The current interest rate is {current_interest_rate}, so we should rebalance"
            )
            interest_rate = self.parameters["interest_rate"]
            if current_interest_rate > interest_rate:
                self.parameters["portfolio"] = [
                    {
                        "symbol": "TQQQ",  # 3x Leveraged Nasdaq
                        "weight": 0.20,
                    },
                    {
                        "symbol": "UPRO",  # 3x Leveraged S&P 500
                        "weight": 0.10,
                    },
                    {
                        "symbol": "UDOW",  # 3x Leveraged Dow Jones
                        "weight": 0.10,
                    },
                    {
                        "symbol": "EDC",  # 3x Leveraged Emerging Markets
                        "weight": 0.10,
                    },
                    {
                        "symbol": "TMF",  # 3x Leveraged Treasury Bonds
                        "weight": 0.30,
                    },
                    {
                        "symbol": "UGL",  # 3x Leveraged Gold
                        "weight": 0.05,
                    },
                    {
                        "symbol": "AGQ",  # 3x Leveraged Silver
                        "weight": 0.05,
                    },
                    {
                        "symbol": "VIXM",  # VIX ETF
                        "weight": 0.10,
                    },
                ]
            else:
                self.parameters["portfolio"] = [
                    {
                        "symbol": "TQQQ",  # 3x Leveraged Nasdaq
                        "weight": 0.20,
                    },
                    {
                        "symbol": "UPRO",  # 3x Leveraged S&P 500
                        "weight": 0.20,
                    },
                    {
                        "symbol": "UDOW",  # 3x Leveraged Dow Jones
                        "weight": 0.20,
                    },
                    {
                        "symbol": "EDC",  # 3x Leveraged Emerging Markets
                        "weight": 0.15,
                    },
                    {
                        "symbol": "TMF",  # 3x Leveraged Treasury Bonds
                        "weight": 0.05,
                    },
                    {
                        "symbol": "UGL",  # 3x Leveraged Gold
                        "weight": 0.05,
                    },
                    {
                        "symbol": "AGQ",  # 3x Leveraged Silver
                        "weight": 0.05,
                    },
                    {
                        "symbol": "VIXM",  # VIX ETF
                        "weight": 0.10,
                    },
                ]

            self.rebalance_portfolio()
            self.log_message(
                f"Next portfolio rebalancing will be in {rebalance_period} day(s)"
            )

        self.log_message("Sleeping until next trading day")
        self.counter += 1

        # Stop for the day, since we are looking at daily momentums
        # self.await_market_to_close()

    def calc_portfolio_weights(self):
        pass

    # =============Helper methods====================

    def rebalance_portfolio(self):
        """Rebalance the portfolio and create orders"""

        orders = []
        for asset in self.parameters["portfolio"]:
            # Get all of our variables from portfolio
            symbol = asset.get("symbol")
            weight = asset.get("weight")
            last_price = self.get_last_price(symbol)

            # Get how many shares we already own
            # (including orders that haven't been executed yet)
            position = self.get_position(symbol)
            quantity = 0
            if position is not None:
                quantity = float(position.quantity)

            # Calculate how many shares we need to buy or sell
            shares_value = self.portfolio_value * weight
            self.log_message(
                f"The current portfolio value is {self.portfolio_value} and the weight needed is {weight}, so we should buy {shares_value}"
            )
            new_quantity = shares_value // last_price
            quantity_difference = new_quantity - quantity
            self.log_message(
                f"Currently own {quantity} shares of {symbol} but need {new_quantity}, so the difference is {quantity_difference}"
            )

            # If quantity is positive then buy, if it's negative then sell
            side = ""
            if quantity_difference > 0:
                side = "buy"
            elif quantity_difference < 0:
                side = "sell"

            # Execute the order if necessary
            if side:
                order = self.create_order(symbol, abs(quantity_difference), side)
                orders.append(order)

        self.submit_orders(orders)


if __name__ == "__main__":
    is_live = False

    if is_live:
        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(AlpacaConfig)
        strategy = DiversifiedLeverageAdjust(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Choose the time from and to which you want to backtest
        backtesting_start = datetime(2012, 1, 1)
        backtesting_end = datetime(2022, 8, 1)

        # Initialize the backtesting object
        print("Starting Backtest...")
        DiversifiedLeverageAdjust.backtest(
            YahooDataBacktesting, backtesting_start, backtesting_end, parameters={}
        )
