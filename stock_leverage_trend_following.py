import datetime

from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.entities import Asset, TradingFee
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader


class StockLeverageTrendFollowing(Strategy):
    parameters = {
        "symbol": "SPY",
        "leverage_symbol": "UPRO",
        "period_length": 17,
    }

    def initialize(self):
        self.sleeptime = "1D"

    def on_trading_iteration(self):
        period_length = self.parameters["period_length"]
        symbol = self.parameters["symbol"]
        leverage_symbol = self.parameters["leverage_symbol"]

        asset = Asset(symbol=symbol, asset_type="stock")
        leverage_asset = Asset(symbol=leverage_symbol, asset_type="stock")
        historical_prices = self.get_historical_prices(
            asset,
            period_length + 1,
            "day",
            quote=self.quote_asset,
            timeshift=datetime.timedelta(minutes=16)
            if self.data_source.SOURCE == "ALPACA"
            else None,  # Alpaca throws an error if we don't do this and don't have a data subscription.
        )
        df = historical_prices.df
        mean = df["close"].mean()
        ema = df["close"].ewm(span=period_length).mean().iloc[-1]
        cur_price = self.get_last_price(asset, quote=self.quote_asset)

        self.log_message(f"Mean: {mean}, EMA: {ema}, Current Price: {cur_price}")

        if cur_price >= ema:
            self.log_message(f"Should own {leverage_symbol}")
            # Check what positions we have
            position = self.get_position(leverage_asset)
            price = self.get_last_price(leverage_asset, quote=self.quote_asset)
            quantity = self.cash / price
            quantity = round(quantity, 1)

            if position is None or position.quantity < quantity:
                self.log_message(f"Position: {position}, Quantity: {quantity}")
                self.log_message(f"Selling all")
                self.sell_all()
                # Buy
                if quantity > 0:
                    self.log_message(
                        f"Buying {quantity} {leverage_symbol} at {cur_price}"
                    )
                    order = self.create_order(
                        leverage_asset,
                        quantity,
                        "buy",
                    )
                    self.submit_order(order)

        else:
            self.log_message(f"Should own {symbol}")
            # Check what positions we have
            position = self.get_position(asset)
            price = self.get_last_price(asset, quote=self.quote_asset)
            quantity = self.cash / price
            quantity = round(quantity, 1)

            if position is None or position.quantity < quantity:
                self.log_message(f"Position: {position}, Quantity: {quantity}")
                self.log_message(f"Selling all")
                self.sell_all()
                # Buy
                if quantity > 0:
                    self.log_message(f"Buying {quantity} {symbol} at {cur_price}")
                    order = self.create_order(
                        asset,
                        quantity,
                        "buy",
                    )
                    self.submit_order(order)


if __name__ == "__main__":
    is_live = False

    if is_live:
        from credentials import ALPACA_CONFIG

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG)

        strategy = StockLeverageTrendFollowing(
            broker=broker,
        )

        trader.add_strategy(strategy)
        strategy_executors = trader.run_all()

    else:
        # Backtest this strategy
        backtesting_start = datetime.datetime(2011, 1, 1)
        backtesting_end = datetime.datetime.now() - datetime.timedelta(days=1)

        # 0.01% trading/slippage fee
        trading_fee = TradingFee(percent_fee=0.0001)

        min = 17
        max = 17
        period_length = min

        while period_length <= max:
            StockLeverageTrendFollowing.backtest(
                YahooDataBacktesting,
                backtesting_start,
                backtesting_end,
                benchmark_asset="SPY",
                buy_trading_fees=[trading_fee],
                sell_trading_fees=[trading_fee],
                parameters={"period_length": period_length},
                name=f"stock-leverage-trend-following-{period_length}",
            )

            period_length += 1
