# Importing
from datetime import datetime
from time import time

import pandas as pd
from credentials import AlpacaConfig
from lumibot.backtesting import PandasDataBacktesting, YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.entities import Asset, Data
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader


# Strategy
class EMA200(Strategy):
    parameters = {
        "pct_cash": 0.05,  # Percentage of our cash to trade for each trade
    }

    def initialize(self):
        self.sleeptime = "1M"

    def on_trading_iteration(self):
        # Get parameters
        pct_cash = self.parameters["pct_cash"]

        # Download historical prices
        data = self.get_historical_prices("SPY", 201, "minute")
        df = data.df

        # 200 EMA
        df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

        # MACD and Signal
        df["macd"] = (
            df["close"].ewm(span=12, adjust=False).mean()
            - df["close"].ewm(span=26, adjust=False).mean()
        )
        df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        price = self.get_last_price("SPY")

        # Check if we are above or below the 200 EMA
        if price > df["ema200"].iloc[-1]:
            # Check that MACD and Signal are below 0
            if df["macd"].iloc[-1] < 0 and df["signal"].iloc[-1] < 0:
                # Check if MACD crossed above Signal
                if (
                    df["macd"].iloc[-1] > df["signal"].iloc[-1]
                    and df["macd"].iloc[-2] < df["signal"].iloc[-2]
                ):
                    if self.get_cash() > 0:
                        # Buy using 1% of our cash
                        # *** You may have to upgrade lumibot for this to work "pip install --upgrade lumibot"
                        purchase_amount = self.get_cash() * pct_cash

                        # Calculate the number of shares we can buy
                        purchase_qty = purchase_amount // price

                        # Buy
                        order = self.create_order("SPY", purchase_qty, "buy")
                        self.submit_order(order)

                        # Put in a take profit order 2% above our entry price
                        limit_price = price * 1.02
                        tp_order = self.create_order(
                            "SPY", purchase_qty, "sell", limit_price=limit_price
                        )
                        self.submit_order(tp_order)

                        # Put in a stop loss order 1% below our entry price
                        stop_price = price * 0.99
                        sl_order = self.create_order(
                            "SPY", purchase_qty, "sell", stop_price=stop_price
                        )
                        self.submit_order(sl_order)

        # Check if we are below the 200 EMA
        if price < df["ema200"].iloc[-1]:
            # Check that MACD and Signal are above 0
            if df["macd"].iloc[-1] > 0 and df["signal"].iloc[-1] > 0:
                # Check if MACD crossed below Signal
                if (
                    df["macd"].iloc[-1] < df["signal"].iloc[-1]
                    and df["macd"].iloc[-2] > df["signal"].iloc[-2]
                ):
                    if self.get_cash() > 0:
                        # Sell using 1% of our cash
                        sell_amount = self.get_cash() * pct_cash

                        # Calculate the number of shares we can sell
                        sell_qty = sell_amount // price

                        # Sell
                        order = self.create_order("SPY", sell_qty, "sell")
                        self.submit_order(order)

                        # Put in a take profit order 2% below our entry price
                        limit_price = price * 0.98
                        tp_order = self.create_order(
                            "SPY", sell_qty, "buy", limit_price=limit_price
                        )
                        self.submit_order(tp_order)

                        # Put in a stop loss order 1% above our entry price
                        stop_price = price * 1.01
                        sl_order = self.create_order(
                            "SPY", sell_qty, "buy", stop_price=stop_price
                        )
                        self.submit_order(sl_order)

    def get_pivot_points(self, df):
        # Calculate the pivot point
        pivot_point = df["close"].sum() / len(df)

        # Calculate the support and resistance levels
        support_1 = pivot_point * 2 - df["close"].max()
        support_2 = pivot_point - df["close"].max() + df["close"].min()
        resistance_1 = pivot_point * 2 - df["close"].min()
        resistance_2 = pivot_point - df["close"].min() + df["close"].max()

        # Create a dictionary with the pivot point and support and resistance levels
        pivot_points = {
            "Pivot Point": pivot_point,
            "Support 1": support_1,
            "Support 2": support_2,
            "Resistance 1": resistance_1,
            "Resistance 2": resistance_2,
        }

        # Return the pivot points as a Pandas dataframe
        return pd.DataFrame(pivot_points, index=[0])


if __name__ == "__main__":
    is_live = False

    if is_live:
        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(AlpacaConfig)
        strategy = EMA200(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Load minute data
        tickers = ["SPY"]

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
        backtesting_start = datetime(2020, 8, 15)
        backtesting_end = datetime(2020, 8, 30)
        EMA200.backtest(
            PandasDataBacktesting,
            backtesting_start,
            backtesting_end,
            pandas_data=my_data,
        )
