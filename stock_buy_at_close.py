# Importing
from datetime import datetime

import pandas as pd
from credentials import ALPACA_CONFIG
from lumibot.backtesting import PandasDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.entities import Asset, Data, TradingFee
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from pytz import timezone


# Strategy
class BuyAtClose(Strategy):
    parameters = {"symbol": "SPY"}

    def initialize(self):
        # Will make on_trading_iteration() run every 180 minutes
        self.sleeptime = "10M"

        self.state = None
        self.done_for_day = False

    def on_trading_iteration(self):
        symbol = self.parameters["symbol"]
        date = self.get_datetime().astimezone(timezone("America/New_York"))

        # Sell in the morning
        if date.hour == 9 and date.minute >= 30 and date.minute <= 45:
            self.sell_all()
            self.done_for_day = False

        # Buy at close
        if (
            date.hour == 15
            and date.minute >= 44
            and date.minute <= 59
            and not self.done_for_day
        ):
            price = self.get_last_price(symbol)
            quantity = self.cash // price
            order = self.create_order(
                symbol,
                quantity,
                "buy",
            )
            self.submit_order(order)

            self.done_for_day = True


if __name__ == "__main__":
    is_live = False

    if is_live:
        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG)
        strategy = BuyAtClose(broker=broker)
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

        # Assuming 0.01% commission/slippage
        trading_fee = TradingFee(percent_fee=0.0001)
        
        symbol = "UPRO"

        # Backtesting
        backtesting_start = datetime(2020, 8, 1)
        backtesting_end = datetime(2022, 11, 1)
        BuyAtClose.backtest(
            PandasDataBacktesting,
            backtesting_start,
            backtesting_end,
            pandas_data=my_data,
            buy_trading_fees=[trading_fee],
            sell_trading_fees=[trading_fee],
            name=f"BuyAtClose_{symbol}",
            parameters={"symbol": symbol},
        )
