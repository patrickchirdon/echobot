import datetime
from decimal import Decimal

import pandas as pd
from lumibot.backtesting import PandasDataBacktesting
from lumibot.entities import Asset, Data, TradingFee
from lumibot.strategies.strategy import Strategy


class CryptoTrendFollowing1(Strategy):
    parameters = {
        "symbol": "BTC",
        "period_length": 17,
    }

    def initialize(self):
        self.sleeptime = "1D"
        self.set_market("24/7")

    def on_trading_iteration(self):
        # Initial idea from on https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4081000
        period_length = self.parameters["period_length"]
        symbol = self.parameters["symbol"]
        asset = Asset(symbol=symbol, asset_type="crypto")
        historical_prices = self.get_historical_prices(
            asset, period_length + 1, "day", quote=self.quote_asset
        )
        df = historical_prices.df
        mean = df["close"].mean()
        ema = df["close"].ewm(span=period_length).mean().iloc[-1]
        cur_price = self.get_last_price(asset, quote=self.quote_asset)

        self.log_message(f"Mean: {mean}, EMA: {ema}, Current price: {cur_price}")

        # Buy the asset if the price is above the mean
        if cur_price >= ema:
            self.log_message(
                f"{cur_price} >= {ema}. Considering to buy {symbol}, but first checking if we have an existing position"
            )
            # Check if we own the asset already
            position = self.get_position(asset)

            # If we don't own the asset or if we don't own enough of it, then buy it
            percentage_owned = 0
            if position is not None:
                value_owned = Decimal(position.quantity) * Decimal(cur_price)
                percentage_owned = value_owned / Decimal(self.portfolio_value)

            self.log_message(f"We own {percentage_owned * 100}% of {symbol}")

            if percentage_owned < 0.95:
                last_price = self.get_last_price(asset, quote=self.quote_asset)
                cash = self.cash * 0.95
                quantity = Decimal(cash / last_price).quantize(Decimal("0.001"))

                self.log_message(f"Buying {quantity} {asset.symbol} @ {last_price}")

                order = self.create_order(
                    asset, quantity, "buy", quote=self.quote_asset
                )
                self.submit_order(order)
            else:
                self.log_message(
                    f"We already own {position.quantity} {asset.symbol}, not going to buy"
                )
        # Sell the asset if the price is below the mean (if we own it)
        else:
            self.log_message(f"{cur_price} < {ema}. Selling {symbol} (if we own any)")
            self.sell_all()


if __name__ == "__main__":
    is_live = False

    if is_live:
        from lumibot.brokers import Alpaca
        from lumibot.traders import Trader

        ALPACA_CONFIG_PAPER = {
            # Put your own Alpaca key here:
            "API_KEY": "PKNEWWNVHY1LGHE3CR55",
            # Put your own Alpaca secret here:
            "API_SECRET": "UzdaYWawdxfapi51iFqQ5oMy0hnq1YsB7S2mDCvv",
            # If you want to go live, you must change this
            "ENDPOINT": "https://paper-api.alpaca.markets",
        }

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG_PAPER)

        strategy = CryptoTrendFollowing1(
            broker=broker,
        )

        trader.add_strategy(strategy)
        strategy_executors = trader.run_all()

    else:
        from lumibot.backtesting import PandasDataBacktesting

        # Backtest this strategy
        backtesting_start = datetime.datetime(2019, 1, 30)
        backtesting_end = datetime.datetime(
            2023, 1, 8
        )  # datetime.datetime.now() - datetime.timedelta(days=1)

        # Load all the data
        symbols = ["ETH", "BTC"]
        pandas_data = {}
        quote_asset = Asset(symbol="USD", asset_type="forex")
        for symbol in symbols:
            # Get the path for the data
            filepath = f"data/crypto/Gemini_{symbol}USD_all_1min.csv"

            # Skip the first row since it's not the data we want
            df = pd.read_csv(filepath)

            # Convert the date column to a datetime object that is timezone aware
            df["date"] = pd.to_datetime(df["date"])
            df["volume"] = df["Volume USD"]
            df = df.set_index("date")
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

        min = 17
        max = 17
        period_length = min
        symbol = "BTC"

        while period_length <= max:
            CryptoTrendFollowing1.backtest(
                PandasDataBacktesting,
                backtesting_start,
                backtesting_end,
                pandas_data=pandas_data,
                benchmark_asset=f"{symbol}-USD",
                quote_asset=quote_asset,
                buy_trading_fees=[trading_fee],
                sell_trading_fees=[trading_fee],
                parameters={
                    "period_length": period_length,
                    "symbol": symbol,
                },
                name=f"{symbol} {period_length} Day Trend Following",
            )

            period_length += 1
