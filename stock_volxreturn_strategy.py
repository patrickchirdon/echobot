# Importing
from datetime import datetime
from time import time

import pandas as pd
from lumibot.backtesting import PandasDataBacktesting, YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.entities import Asset, Data
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

from credentials import AlpacaConfig


# Strategy
class VolXReturn(Strategy):
    parameters = {"safe_symbol": "SPY", "leveraged_symbol": "UPRO", "length": 30}

    def initialize(self):
        # Will make on_trading_iteration() run every 180 minutes
        self.sleeptime = "1M"

        self.state = None
        self.done_for_day = False

    def on_trading_iteration(self):
        date = self.get_datetime()

        # self.cash
        # self.portfolio_value
        # positions = self.get_positions()
        safe_symbol = self.parameters["safe_symbol"]
        leveraged_symbol = self.parameters["leveraged_symbol"]
        # leveraged_symbol_price = self.get_last_price(leveraged_symbol)
        # safe_symbol_price = self.get_last_price(safe_symbol)

        if date.hour <= 9 and date.minute <= 30:
            self.done_for_day = False

        if date.hour >= 15 and date.minute >= 50 and not self.done_for_day:
            length = self.parameters["length"]

            bars = self.get_historical_prices(safe_symbol, length + 1, "day")
            df = bars.df

            df["Return"] = df["close"].pct_change()
            df["VolxReturn"] = df["volume"] * df["Return"]
            df["VolxReturn_30D_mean"] = df.loc[:, "VolxReturn"].rolling(30).mean()

            current = df.iloc[-1]

            if (
                current["VolxReturn"] < current["VolxReturn_30D_mean"]
                and self.state != "long"
            ):
                self.sell_all()

                price = self.get_last_price(leveraged_symbol)
                quantity = self.portfolio_value // price
                order = self.create_order(leveraged_symbol, quantity, "buy")
                self.submit_order(order)

                self.state = "long"

            elif (
                current["VolxReturn"] >= current["VolxReturn_30D_mean"]
                and self.state != "safe"
            ):
                self.sell_all()

                price = self.get_last_price(safe_symbol)
                quantity = self.portfolio_value // price
                order = self.create_order(safe_symbol, quantity, "buy")
                self.submit_order(order)

                self.state = "safe"

            # self.await_market_to_close()
            self.done_for_day = True


if __name__ == "__main__":
    is_live = False

    if is_live:
        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(AlpacaConfig)
        strategy = VolXReturn(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Load minute data
        tickers = ["SPY", "UPRO"]

        my_data = {}
        for ticker in tickers:
            df = pd.read_csv(f"data/{ticker}_1min.csv")
            df = df.set_index("time")
            df.index = pd.to_datetime(df.index)
            asset = Asset(
                symbol=ticker,
                asset_type="stock",
            )
            my_data[asset] = Data(
                asset,
                df,
                timestep="minute",
            )

        # Backtesting
        backtesting_start = datetime(2020, 9, 1)
        backtesting_end = datetime(2022, 7, 1)
        VolXReturn.backtest(
            PandasDataBacktesting,
            backtesting_start,
            backtesting_end,
            pandas_data=my_data,
        )
