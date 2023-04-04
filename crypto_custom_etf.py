import datetime
import math
from decimal import Decimal

import pandas as pd
from credentials import ALPACA_CONFIG, KUCOIN_CONFIG
from lumibot.backtesting import PandasDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.brokers.ccxt import Ccxt
from lumibot.entities import Asset, Data, TradingFee
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

"""
Strategy Description

This strategy will buy a few of the top cryptocurrencies and rebalance the portfolio often.
"""


class CustomETF(Strategy):
    # =====Overloading lifecycle methods=============

    parameters = {
        "portfolio": [
            {
                "symbol": Asset(symbol="BTC", asset_type="crypto"),
                "weight": 0.32,
            },
            {
                "symbol": Asset(symbol="ETH", asset_type="crypto"),
                "weight": 0.32,
            },
            {
                "symbol": Asset(symbol="LTC", asset_type="crypto"),
                "weight": 0.32,
            },
        ],
    }

    def initialize(self):
        self.sleeptime = "10D"
        self.set_market("24/7")  # Need to do for crypto!

    def on_trading_iteration(self):
        self.rebalance_portfolio()

    # =============Helper methods===================

    def rebalance_portfolio(self):
        """Rebalance the portfolio and create orders"""
        orders = []
        for asset in self.parameters["portfolio"]:
            # Get all of our variables from portfolio
            asset_to_trade = asset.get("symbol")
            weight = asset.get("weight")
            quote = self.quote_asset
            symbol = asset_to_trade.symbol
            dt = self.get_datetime()
            last_price = self.get_last_price(asset_to_trade, quote=quote)

            if last_price is None:
                self.log_message(
                    f"Couldn't get a price for {symbol} self.get_last_price() returned None"
                )
                continue

            self.log_message(
                f"Last price for {symbol} is {last_price:,f}, and our weight is {weight}. Current portfolio value is {self.portfolio_value}"
            )

            # Get how many shares we already own
            # (including orders that haven't been executed yet)
            quantity = Decimal(str(self.get_asset_potential_total(asset_to_trade)))

            # Calculate how many shares we need to buy or sell
            shares_value = self.portfolio_value * weight
            new_quantity = Decimal(str(shares_value / last_price))

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

            # Execute the
            # order if necessary
            if side:
                qty = abs(quantity_difference)

                # Trim to 2 decimal places because the API only accepts
                # 2 decimal places for some assets. This could be done better
                # on an asset by asset basis. e.g. for BTC, we want to use 4
                # decimal places at Alpaca, or a 0.0001 increment. See other coins
                # at Alpaca here: https://alpaca.markets/docs/trading/crypto-trading/
                qty_trimmed = qty.quantize(Decimal("0.001"), rounding="ROUND_DOWN")

                if qty_trimmed > 0:
                    order = self.create_order(
                        asset_to_trade,
                        qty_trimmed,
                        side,
                        quote=quote,
                    )
                    orders.append(order)

        if len(orders) == 0:
            self.log_message("No orders to execute")

        # Execute sell orders first so that we have the cash to buy the new shares
        for order in orders:
            if order.side == "sell":
                self.submit_order(order)

        # Sleep for 5 seconds to make sure the sell orders are filled
        self.sleep(5)

        # Execute buy orders
        for order in orders:
            if order.side == "buy":
                self.submit_order(order)


if __name__ == "__main__":
    # True if you want to trade live or False if you want to backtest
    is_live = True

    if is_live:
        ####
        # Live Trading
        ####

        trader = Trader()

        # broker = Ccxt(KUCOIN_CONFIG)
        # quote_asset = Asset(symbol="USDT", asset_type="crypto")

        broker = Alpaca(ALPACA_CONFIG)
        quote_asset = Asset(symbol="USD", asset_type="forex")

        strategy = CustomETF(broker, quote_asset=quote_asset)

        trader.add_strategy(strategy)
        strategies = trader.run_all()

    else:
        ####
        # Backtesting
        ####

        # Choose your initial conditions
        backtesting_start = datetime.datetime(2021, 1, 15)
        backtesting_end = datetime.datetime(2021, 12, 31)
        benchmark_asset = "BTC-USD"

        # Load all the data
        symbols = ["BTC", "ETH", "LTC"]
        pandas_data = {}
        for symbol in symbols:
            # Get the path for the data
            filepath = f"Day 11/code/data/Gemini_{symbol}USD_2021_1min.csv"

            # Skip the first row since it's not the data we want
            df = pd.read_csv(filepath, skiprows=1)

            # Convert the date column to a datetime object that is timezone aware
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
            df.index = df.index.tz_localize("UTC")

            # Create a Data object from the Pandas DataFrame and add it to the
            # pandas_data dictionary
            base_asset = Asset(symbol=symbol, asset_type="crypto")
            quote_asset = Asset(symbol="USD", asset_type="forex")
            pandas_data[(base_asset, quote_asset)] = Data(
                base_asset, df, timestep="minute", quote=quote_asset
            )

        trading_fee = TradingFee(percent_fee=0.001)  # 0.1% fee
        # Run the backtest
        CustomETF.backtest(
            PandasDataBacktesting,
            backtesting_start,
            backtesting_end,
            pandas_data=pandas_data,
            benchmark_asset=benchmark_asset,
            quote_asset=Asset(symbol="USD", asset_type="forex"),
            buy_trading_fees=[trading_fee],
            sell_trading_fees=[trading_fee],
        )
