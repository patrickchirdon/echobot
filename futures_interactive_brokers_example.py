from datetime import date
from decimal import Decimal

from credentials import INTERACTIVE_BROKERS_CONFIG
from lumibot.brokers import InteractiveBrokers
from lumibot.entities import Asset
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader


class FuturesImportantFunctions(Strategy):
    # =====Overloading lifecycle methods=============

    def initialize(self):
        # Set the time between trading iterations
        self.sleeptime = "30S"
        self.set_market("us_futures")

    def on_trading_iteration(self):
        self.base = Asset(
            symbol="ES",
            asset_type="future",
            expiration=date(2023, 3, 17),
        )

        ############
        # Orders
        ############

        # Place a market order to buy 1 contract of the base asset
        order = self.create_order(
            asset=self.base,
            quantity=1,
            side="buy",
        )
        self.submit_order(order)

        # Place a limit order to sell 1 contract of the base asset
        order = self.create_order(
            asset=self.base,
            quantity=1,
            side="sell",
            limit_price=Decimal("100"),
        )
        self.submit_order(order)

        ############
        # Positions
        ############

        positions = self.get_positions()
        for position in positions:
            self.log_message(f"We currently own {position.quantity} of {position.asset}.")

    def on_filled_order(self, position, order, price, quantity, multiplier):
        self.log_message(
            f"Order {order} was filled at {price} for {quantity} contracts."
        )
        
        self.last_filled_price = price

if __name__ == "__main__":
    trader = Trader()
    broker = InteractiveBrokers(INTERACTIVE_BROKERS_CONFIG)

    strategy = FuturesImportantFunctions(
        broker=broker,
    )

    trader.add_strategy(strategy)
    strategy_executors = trader.run_all()
