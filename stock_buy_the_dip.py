from datetime import datetime
from uuid import uuid4

from credentials import AlpacaConfigPaper2
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

"""
Strategy Description

This strategy will normally invest in a 60/40 stock/bond ratio, but 
will change that mix after a big drop in the market.
"""

normal_portfolio = [
    {
        "symbol": "UPRO",  # 3x Leveraged S&P 500
        "weight": 0.60,
    },
    {
        "symbol": "TMF",  # 3x Leveraged Treasury Bonds
        "weight": 0.40,
    },
]

dip_portfolio = [
    {
        "symbol": "UPRO",  # 3x Leveraged S&P 500
        "weight": 1,
    },
]


class BuyTheDip(Strategy):
    # Set the default parameters for the strategy
    parameters = {
        "symbol_to_watch": "SPY",
        "big_drop_level": -0.03,
        "normal_portfolio": normal_portfolio,
        "dip_portfolio": dip_portfolio,
        "rebalance_period": 4,
    }

    # =====Overloading lifecycle methods=============
    def initialize(self):

        # Setting the waiting period (in days) and the counter
        self.rebalance_period = self.parameters["rebalance_period"]
        self.counter = 0

        # There is only one trading operation per day
        # no need to sleep between iterations
        self.sleeptime = 0

        # Initializing the portfolio variable with the assets and proportions we want to own
        self.initialized = False

        self.yesterdays_symbol_to_watch_price = None

    def on_trading_iteration(self):
        symbol_to_watch = self.parameters["symbol_to_watch"]
        big_drop_level = self.parameters["big_drop_level"]

        # The default portfolio is the normal one
        portfolio_weights = self.parameters["normal_portfolio"]

        # Check if we should change the portfolio weighting
        symbol_to_watch_price = self.get_last_price(symbol_to_watch)
        if self.yesterdays_symbol_to_watch_price is not None:
            price_change = symbol_to_watch_price - self.yesterdays_symbol_to_watch_price
            price_change_pct = price_change / self.yesterdays_symbol_to_watch_price

            # If the price has dropped by more than the big_drop_level
            # Then we should change the portfolio to the dip one
            if price_change_pct <= big_drop_level:
                portfolio_weights = self.parameters["dip_portfolio"]

        # If the target number of days (period) has passed, rebalance the portfolio
        if self.counter == self.rebalance_period or self.counter == 0:
            self.counter = 0
            self.rebalance_portfolio(portfolio_weights)
            self.log_message(
                f"Next portfolio rebalancing will be in {self.rebalance_period} day(s)"
            )

        self.log_message("Sleeping untill next trading day")
        self.counter += 1

        self.yesterdays_symbol_to_watch_price = symbol_to_watch_price

    # =============Helper methods====================

    def rebalance_portfolio(self, portfolio_weights):
        """Rebalance the portfolio and create orders"""

        orders = []
        for asset in portfolio_weights:
            # Get all of our variables from portfolio
            symbol = asset.get("symbol")
            weight = asset.get("weight")
            last_price = self.get_last_price(symbol)
            if last_price is None:
                self.log_message(
                    f"Pricing data for {symbol} is not available, self.get_last_price() returned None"
                )
                continue

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
        trader = Trader()
        broker = Alpaca(AlpacaConfigPaper2)
        strategy_name = str(uuid4())

        strategy = BuyTheDip(
            broker=broker,
        )

        trader.add_strategy(strategy)
        strategy_executors = trader.run_all()

    else:
        backtesting_start = datetime(2016, 1, 1)
        backtesting_end = datetime(2022, 4, 1)

        print("Starting Backtest...")
        BuyTheDip.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
        )
