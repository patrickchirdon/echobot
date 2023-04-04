import datetime
from decimal import Decimal

from credentials import ALPACA_CONFIG
from lumibot.brokers import Alpaca
from lumibot.entities import Asset
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader


class ImportantFunctions(Strategy):
    # =====Overloading lifecycle methods=============

    def initialize(self):
        # Set the time between trading iterations
        self.sleeptime = "30S"

        # Set the market to 24/7 since those are the hours for the crypto market
        self.set_market("24/7")

    def on_trading_iteration(self):
        ###########################
        # Placing an Order
        ###########################

        # Define the base and quote assets for our transactions
        base = Asset(symbol="BTC", asset_type="crypto")
        quote = self.quote_asset

        # Market Order
        mkt_order = self.create_order(base, 0.1, "buy", quote=quote)
        self.submit_order(mkt_order)

        # Limit Order
        lmt_order = self.create_order(base, 0.1, "buy", quote=quote, limit_price=10000)
        self.submit_order(lmt_order)

        # Stop Order
        stp_order = self.create_order(
            base, 0.1, "buy", quote=quote, stop_price=Decimal(20000) - Decimal(1)
        )
        self.submit_order(stp_order)

        # OCO Order
        oco_order = self.create_order(
            base,
            0.1,
            "buy",
            quote=quote,
            take_profit_price=Decimal(20000) - Decimal(1),
            stop_loss_price=Decimal(20000) + Decimal(1),
            position_filled=True,
        )
        self.submit_order(oco_order)

        ###########################
        # Getting Historical Data
        ###########################

        # Get the historical prices for our base/quote pair
        bars = self.get_historical_prices(base, 100, "minute", quote=quote)
        if bars is not None:
            df = bars.df
            max_price = df["close"].max()
            self.log_message(f"Max price for {base} was {max_price}")
            # self.log_message(f"Last price for {base} was {bars.get_last_price()}")

        ###########################
        # Positions and Orders
        ###########################

        # Get all the positions that we own, including cash
        positions = self.get_positions()
        for position in positions:
            self.log_message(f"Position: {position}")
            asset = position.asset

            symbol = asset.symbol
            self.log_message(f"we own {position.quantity} shares of {symbol}")
            # Do whatever you need to do with the position

        # Get one specific position
        asset_to_get = Asset(symbol="BTC", asset_type="crypto")
        position = self.get_position(asset_to_get)

        # Get all of the outstanding orders
        orders = self.get_orders()
        for order in orders:
            self.log_message(f"Order: {order}")
            # Do whatever you need to do with the order

        # Get one specific order
        order = self.get_order(mkt_order.identifier)

        ###########################
        # Other Useful Functions
        ###########################

        # Get the current (last) price for the base/quote pair
        last_price = self.get_last_price(base, quote=quote)
        self.log_message(
            f"Last price for {base}/{quote} was {last_price}", color="green"
        )

        dt = self.get_datetime()
        self.log_message(f"The current datetime is {dt}")
        self.log_message(f"The current time is {dt.time()}")
        if dt.time() > datetime.time(hour=9, minute=30):
            self.log_message("It's after 9:30am")

        # Get the value of the entire portfolio, including positions and cash
        portfolio_value = self.portfolio_value
        # Get the amount of cash in the account (the amount in the quote_asset)
        cash = self.cash

        self.log_message("done")


if __name__ == "__main__":
    trader = Trader()
    broker = Alpaca(ALPACA_CONFIG)

    strategy = ImportantFunctions(
        broker=broker,
    )

    trader.add_strategy(strategy)
    strategy_executors = trader.run_all()
