from datetime import datetime

from credentials import ALPACA_CONFIG
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

"""
Strategy Description

This strategy buys stocks that are trending up based on two EMAs. It sells all the stocks that are not trending up that it currently owns
and buys the stocks that are trending up that it does not currently own.
"""


class StockDoubleEMATrending(Strategy):
    parameters = {
        "symbols": ["AAPL", "SPY", "TSLA", "NVDA", "MSFT"],
        "ema1_short_length": 12,
        "ema1_long_length": 32,
        "ema2_short_length": 12,
        "ema2_long_length": 26,
    }

    def initialize(self):
        # There is only one trading operation per day
        # No need to sleep between iterations
        self.sleeptime = "1D"

    def on_trading_iteration(self):
        symbols = self.parameters["symbols"]
        ema1_short_length = self.parameters["ema1_short_length"]
        ema1_long_length = self.parameters["ema1_long_length"]
        ema2_short_length = self.parameters["ema2_short_length"]
        ema2_long_length = self.parameters["ema2_long_length"]

        symbols_trending_up = []

        # Check which symbols are trending up
        for symbol in symbols:
            # Get the data for the symbol
            length_needed = max(ema1_long_length, ema2_long_length)
            data = self.get_historical_prices(symbol, length_needed, "day")
            df = data.df

            # Calculate the EMAs
            df["ema1_short"] = df["close"].ewm(span=ema1_short_length).mean()
            current_ema1_short = df["ema1_short"].iloc[-1]
            df["ema1_long"] = df["close"].ewm(span=ema1_long_length).mean()
            current_ema1_long = df["ema1_long"].iloc[-1]
            df["ema2_short"] = df["close"].ewm(span=ema2_short_length).mean()
            current_ema2_short = df["ema2_short"].iloc[-1]
            df["ema2_long"] = df["close"].ewm(span=ema2_long_length).mean()
            current_ema2_long = df["ema2_long"].iloc[-1]

            if (
                current_ema1_short > current_ema1_long
                and current_ema2_short > current_ema2_long
            ):
                # The symbol is trending up, add it to the list
                symbols_trending_up.append(symbol)

        # Sell all the symbols that are not trending up that we currently own
        positions = self.get_positions()
        for position in positions:
            if (
                position.symbol not in symbols_trending_up
                and position.asset.asset_type == "stock"
            ):
                order = self.create_order(position.symbol, position.quantity, "sell")
                self.submit_order(order)

        if len(symbols_trending_up) > 0:

            amount_to_invest_per_symbol = self.get_portfolio_value() / len(
                symbols_trending_up
            )

            # Sell any extra shares of symbols that are trending up because we might own too much of them
            for symbol in symbols_trending_up:
                position = self.get_position(symbol)
                if position is not None:
                    current_price = self.get_last_price(symbol)
                    qty_we_should_own = amount_to_invest_per_symbol // current_price
                    amount_to_sell = float(position.quantity) - qty_we_should_own
                    if amount_to_sell > 0:
                        order = self.create_order(symbol, amount_to_sell, "sell")
                        self.submit_order(order)

            # Buy the symbols that are trending up
            for symbol in symbols_trending_up:
                position = self.get_position(symbol)
                price = self.get_last_price(symbol)
                value_of_position = 0
                if position is not None:
                    value_of_position = float(position.quantity) * price

                amount_to_invest = amount_to_invest_per_symbol - value_of_position
                qty_to_buy = amount_to_invest // price
                if qty_to_buy > 0:
                    order = self.create_order(symbol, qty_to_buy, "buy")
                    self.submit_order(order)


if __name__ == "__main__":
    is_live = False

    if is_live:
        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG)
        strategy = StockDoubleEMATrending(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Choose the time from and to which you want to backtest
        backtesting_start = datetime(2012, 1, 1)
        backtesting_end = datetime(2013, 1, 1)

        # Initialize the backtesting object
        print("Starting Backtest...")
        StockDoubleEMATrending.backtest(
            YahooDataBacktesting, backtesting_start, backtesting_end, parameters={}
        )
