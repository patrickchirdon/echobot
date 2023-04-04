from datetime import timedelta

from lumibot.data_sources import AlpacaData
from lumibot.strategies.strategy import Strategy

"""
Strategy Description

Buys the best performing asset from self.symbols over self.period number of minutes.
For example, if TSLA increased 0.03% in the past two minutes, but SPY, GLD, TLT and MSFT only 
increased 0.01% in the past two minutes, then we will buy TSLA.
"""


class IntradayMomentum(Strategy):
    # =====Overloading lifecycle methods=============

    def initialize(
        self, period=2, symbols=["SPY", "GLD", "TLT", "MSFT", "TSLA", "AAPL"]
    ):
        # Setting the momentum period (in minutes)
        self.period = period

        # Set how often (in minutes) we should be running on_trading_iteration
        self.sleeptime = 1

        # Set the symbols that we want to be monitoring
        self.symbols = symbols

        # Initialize our variables
        self.asset = None
        self.quantity = 0

    def on_trading_iteration(self):
        # Get the momentums of all the assets we are tracking
        momentums = self.get_assets_momentums()

        # Get the asset with the highest return in our period
        # (aka the highest momentum)66
        momentums.sort(key=lambda x: x.get("return"))
        best_asset = momentums[-1].get("symbol")
        self.log_message("%s best symbol." % best_asset)

        # If the asset with the highest momentum has changed, buy the new asset
        if best_asset != self.asset:
            # Sell the current asset that we own
            if self.asset:
                self.log_message(f"Swapping {self.asset} for {best_asset}.")
                order = self.create_order(self.asset, self.quantity, "sell")
                self.submit_order(order)

            # Calculate the quantity and send the buy order for the new asset
            self.asset = best_asset
            best_asset_price = [
                m["price"] for m in momentums if m["symbol"] == best_asset
            ][0]
            self.quantity = self.portfolio_value // best_asset_price

            order = self.create_order(self.asset, self.quantity, "buy")
            self.submit_order(order)
        else:
            self.log_message(f"Keeping {self.quantity} shares of {self.asset}")

    def before_market_closes(self):
        # Make sure that we sell everything before the market closes
        self.sell_all()

    def on_abrupt_closing(self):
        self.sell_all()

    def on_bot_crash(self, error):
        self.sell_all()

    # =============Helper methods====================

    def get_assets_momentums(self):
        """
        Gets the momentums (the percentage return) for all the assets we are tracking,
        over the time period set in self.period
        """
        momentums = []
        for symbol in self.symbols:
            # Get the return for symbol over self.period minutes
            bars_set = self.get_symbol_bars(symbol, self.period + 1, "minute")
            symbol_df = bars_set.df
            symbol_momentum = bars_set.get_momentum()

            self.log_message(
                "%s has a return value of %.2f%% over the last %d minutes(s)."
                % (symbol, 100 * symbol_momentum, self.period)
            )

            momentums.append(
                {
                    "symbol": symbol,
                    "price": bars_set.get_last_price(),
                    "return": symbol_momentum,
                }
            )

        return momentums
