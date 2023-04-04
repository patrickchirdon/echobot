# Importing
from datetime import datetime

import pandas as pd
from lumibot.backtesting import YahooDataBacktesting
from lumibot.entities import Asset, Data, TradingFee
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from pytz import timezone


# Strategy
class LeverageWhenDown(Strategy):
    parameters = {
        "symbol": "SPY",
        "leverage_symbol": "UPRO",
        "lookback_days": 300,
        "drop_percent": 0.2,
    }

    def initialize(self):
        # Will make on_trading_iteration() run every 180 minutes
        self.sleeptime = "1D"

        self.state = None

    def on_trading_iteration(self):
        symbol = self.parameters["symbol"]
        leverage_symbol = self.parameters["leverage_symbol"]
        lookback_days = self.parameters["lookback_days"]
        drop_percent = self.parameters["drop_percent"]
        dt = self.get_datetime().astimezone(timezone("America/New_York"))

        asset = Asset(symbol=symbol, asset_type="stock")
        leverage_asset = Asset(symbol=leverage_symbol, asset_type="stock")

        historical_prices = self.get_historical_prices(
            asset, lookback_days + 1, "day", quote=self.quote_asset
        )
        df = historical_prices.df
        max = df["close"].max()
        ema = df["close"].ewm(span=lookback_days).mean().iloc[-1]
        cur_price = self.get_last_price(asset, quote=self.quote_asset)
        drop_threshold_price = max * (1 - drop_percent)

        if cur_price <= drop_threshold_price:
            # Check what positions we have
            position = self.get_position(leverage_asset)
            price = self.get_last_price(leverage_asset, quote=self.quote_asset)
            quantity = self.cash // price

            if position is None or position.quantity < quantity:
                self.sell_all()
                # Buy
                if quantity > 0:
                    order = self.create_order(
                        leverage_asset,
                        quantity,
                        "buy",
                    )
                    self.submit_order(order)

        else:
            # Check what positions we have
            position = self.get_position(asset)
            price = self.get_last_price(asset, quote=self.quote_asset)
            quantity = self.cash // price

            if position is None or position.quantity < quantity:
                self.sell_all()
                # Buy
                if quantity > 0:
                    order = self.create_order(
                        asset,
                        quantity,
                        "buy",
                    )
                    self.submit_order(order)


if __name__ == "__main__":
    is_live = False

    if is_live:
        from lumibot.brokers import Alpaca

        from credentials import AlpacaConfig

        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(AlpacaConfig)
        strategy = LeverageWhenDowm(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Assuming 0.01% commission/slippage
        trading_fee = TradingFee(percent_fee=0.0001)

        # Backtesting
        backtesting_start = datetime(2009, 7, 1)
        backtesting_end = datetime(2022, 11, 1)
        LeverageWhenDown.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            buy_trading_fees=[trading_fee],
            sell_trading_fees=[trading_fee],
        )
