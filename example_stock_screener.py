from datetime import datetime, timedelta

import quandl
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies import Strategy
from lumibot.traders import Trader

from credentials import AlpacaConfig, QuandlConfig

quandl.ApiConfig.api_key = QuandlConfig.API_KEY


# A simple strategy that buys AAPL on the first day
class MyStrategy(Strategy):
    def initialize(self):
        self.sleeptime = "1D"

    def before_market_opens(self):
        self.got_funding_volume = False
        # Check if we are backting, if so only get it once
        if self.is_backtesting and not self.first_iteration:
            self.got_funding_volume = True

        if not self.got_funding_volume:
            self.funding_volume = quandl.get("FRED/OBFRVOL")

    def on_trading_iteration(self):
        dt = self.get_datetime()
        # Get the funding volume for today
        row = self.funding_volume.loc[(self.funding_volume.index.date == dt.date())]

        # Error checking
        if len(row) > 0:
            funding_vol = row.iloc[-1]["Value"]
        else:
            funding_vol = 99999999

        # Trading logic
        if funding_vol < 100:
            aapl_price = self.get_last_price("AAPL")
            quantity = self.cash // aapl_price
            order = self.create_order("AAPL", quantity, "buy")
            self.submit_order(order)

        else:
            self.sell_all()


###
# Backtest
###

# Pick the dates that you want to start and end your backtest
# and the allocated budget
backtesting_start = datetime(2020, 1, 1)
backtesting_end = datetime(2022, 3, 30)

# Run the backtest
MyStrategy.backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end,
)


###
# Live Trading
###

broker = Alpaca(AlpacaConfig)
strategy = MyStrategy(broker=broker)
trader = Trader()
trader.add_strategy(strategy)
trader.run_all()
