from datetime import datetime
from decimal import Decimal

import pandas as pd
from credentials import ALPACA_CONFIG
from lumibot.backtesting import PandasDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.entities import Asset, Data, TradingFee
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

"""
Strategy Description

This strategy buys crypto that are trending up based on two EMAs. It sells all the cryptos that are not trending up that it currently owns
and buys the cryptos that are trending up that it does not currently own.
"""


class CryptoDoubleEMATrending(Strategy):
    parameters = {
        "symbols": ["BTC", "ETH", "LTC"],
        "ema1_short_length": 12,
        "ema1_long_length": 32,
        "ema2_short_length": 12,
        "ema2_long_length": 26,
    }

    def initialize(self):
        # There is only one trading operation per day
        # No need to sleep between iterations
        self.sleeptime = "1D"
        self.set_market("24/7")

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
            length_needed = (
                max(ema1_long_length, ema2_long_length) * 60 * 24
            )  # Convert days to minutes
            asset = Asset(symbol=symbol, asset_type="crypto")
            data = self.get_historical_prices(asset, length_needed, "minute")
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

        self.log_message(f"Symbols trending up: {symbols_trending_up}")

        # Sell all the symbols that are not trending up that we currently own
        positions = self.get_positions()
        for position in positions:
            if (
                position.symbol not in symbols_trending_up
                and position.asset.asset_type == "crypto"
            ):
                asset = Asset(symbol=position.symbol, asset_type="crypto")
                order = self.create_order(asset, position.quantity, "sell")
                self.submit_order(order)

        if len(symbols_trending_up) > 0:
            amount_to_invest_per_symbol = self.get_portfolio_value() / len(
                symbols_trending_up
            )

            # Sell any extra shares of symbols that are trending up because we might own too much of them
            for symbol in symbols_trending_up:
                asset = Asset(symbol=symbol, asset_type="crypto")

                position = self.get_position(asset)
                if position is not None:
                    self.log_message(f"Position for {symbol} is {position.quantity}")
                    current_price = self.get_last_price(asset, quote=self.quote_asset)
                    qty_we_should_own = amount_to_invest_per_symbol // current_price
                    amount_to_sell = float(position.quantity) - qty_we_should_own
                    if amount_to_sell > 0:
                        order = self.create_order(asset, amount_to_sell, "sell")
                        self.submit_order(order)
                else:
                    self.log_message(f"Position for {symbol} is None")

            # Buy the symbols that are trending up
            for symbol in symbols_trending_up:
                asset = Asset(symbol=symbol, asset_type="crypto")

                position = self.get_position(asset)
                price = self.get_last_price(asset, quote=self.quote_asset)
                value_of_position = 0
                if position is not None:
                    value_of_position = float(position.quantity) * price

                amount_to_invest = amount_to_invest_per_symbol - value_of_position
                qty_to_buy = Decimal(amount_to_invest) / Decimal(price)
                qty_to_buy_quantize = qty_to_buy.quantize(
                    Decimal("1.00")
                )  # Round to 2 decimal places
                if qty_to_buy_quantize > 0:
                    order = self.create_order(asset, qty_to_buy_quantize, "buy")
                    self.submit_order(order)


if __name__ == "__main__":
    is_live = True

    if is_live:
        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG)
        strategy = CryptoDoubleEMATrending(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Backtest this strategy
        backtesting_start = datetime(2021, 2, 2)
        backtesting_end = datetime(2021, 12, 31)

        # Load all the data
        symbols = ["ETH", "BTC", "LTC"]
        pandas_data = {}
        quote_asset = Asset(symbol="USD", asset_type="forex")
        for symbol in symbols:
            # Get the path for the data
            filepath = f"data/crypto/Gemini_{symbol}USD_2021_1min.csv"

            # Skip the first row since it's not the data we want
            df = pd.read_csv(filepath, skiprows=1)

            # Convert the date column to a datetime object that is timezone aware
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
            df.index = df.index.tz_localize("UTC")

            # Create a Data object from the Pandas DataFrame and add it to the
            # pandas_data dictionary
            base_asset = Asset(symbol=symbol, asset_type="crypto")
            pandas_data[(base_asset, quote_asset)] = Data(
                base_asset, df, timestep="minute", quote=quote_asset
            )

        # 0.1% fee, loosely based on Kucoin (might actually be lower bc we're trading a lot)
        # https://www.kucoin.com/vip/level
        trading_fee = TradingFee(percent_fee=0.001)

        CryptoDoubleEMATrending.backtest(
            PandasDataBacktesting,
            backtesting_start,
            backtesting_end,
            pandas_data=pandas_data,
            benchmark_asset=f"BTC-USD",
            quote_asset=quote_asset,
            buy_trading_fees=[trading_fee],
            sell_trading_fees=[trading_fee],
        )
