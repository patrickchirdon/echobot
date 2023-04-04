import random

from lumibot.brokers import Alpaca
from lumibot.entities import Asset
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

from credentials import AlpacaConfig

"""
Strategy Description

Buys the best performing assets from self.symbols over self.momentum_length number of minutes.
For example, if TSLA increased 0.03% in the past two minutes, but SPY, GLD, TLT and MSFT only 
increased 0.01% in the past two minutes, then we will buy TSLA.
"""


class FastTrading(Strategy):

    # =====Overloading lifecycle methods=============
    def initialize(self, max_assets=5):

        # Set how often (in seconds) we should be running on_trading_iteration
        self.sleeptime = "5S"

        # Set the symbols that we want to be monitoring
        self.symbols = [
            "SPY",
            "GLD",
            "TLT",
            "MSFT",
            "TSLA",
            "MCHI",
            "SPXL",
            "SPXS",
            "TUEM",
            "TQQQ",
            "EDC",
            "UGL",
            "TMF",
            "XVZ",
        ]

        # Set up assets, orders, positions.
        self.assets = []
        for symbol in self.symbols:
            asset = Asset(symbol=symbol, asset_type="stock")
            self.assets.append(asset)

        # Set up order dict. Will hold active orders.
        self.orders = list()

        # Positions. Will track positions, held, sold or bought.
        self.trade_positions = list()

        # Initialize our variables
        self.max_assets = min(max_assets, len(self.assets))

        self.is_buy_iteration = False

    def on_trading_iteration(self):
        if self.is_buy_iteration:
            # Buying assets
            assets_to_buy = []
            for x in range(self.max_assets):
                assets_to_buy.append(random.choice(self.assets))

            for asset in assets_to_buy:
                trade_cash = self.cash / self.max_assets
                last_price = self.get_last_price(asset)
                quantity = trade_cash // last_price

                self.log_message(f"Buying {quantity} shares of {asset.symbol}.")
                if quantity > 0:
                    order = self.create_order(asset, quantity, "buy")
                    self.submit_order(order)

        else:
            # Selling assets
            self.sell_all()

        self.log_message(
            f"At end of iteration: Cash: {self.cash:7.2f}, Value: {self.portfolio_value:7.2f}, "
        )
        self.is_buy_iteration = not self.is_buy_iteration

    def before_market_closes(self):
        # Make sure that we sell everything before the market closes
        self.sell_all()
        self.orders = list()
        self.trade_positions = list()

    def on_abrupt_closing(self):
        self.sell_all()


if __name__ == "__main__":
    trader = Trader()
    broker = Alpaca(AlpacaConfig)
    strategy = FastTrading(broker=broker)
    trader.add_strategy(strategy)
    trader.run_all()
