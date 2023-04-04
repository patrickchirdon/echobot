from lumibot.strategies.strategy import Strategy


class SellIfDown(Strategy):
    # =====Overloading lifecycle methods=============
    def initialize(self, buy_after_days=30, change_threshold=-0.03, buy_symbol="SPY"):
        # Set the initial variables or constants

        # Built in Variables
        self.sleeptime = "1D"  # Could be S, M or D

        # Our custom parameters
        self.buy_symbol = buy_symbol
        self.change_threshold = change_threshold
        self.buy_after_days = buy_after_days

        # Variables for making the strategy work
        self.counter = self.buy_after_days
        self.previous_price = None

    def on_trading_iteration(self):
        # What to do each iteration (every self.sleeptime minutes)
        current_price = self.get_last_price(self.buy_symbol)
        previous_price = self.previous_price

        price_change = 0
        if previous_price is not None:
            price_change = (current_price / previous_price) - 1

        if price_change < self.change_threshold:
            self.sell_all()
            self.counter = 0

        elif self.counter == self.buy_after_days:
            quantity = self.portfolio_value // current_price
            buy_order = self.create_order(self.buy_symbol, quantity, "buy")
            self.submit_order(buy_order)

        # Get the last price that our symbol traded at and save it
        self.previous_price = current_price

        # Increment our counter
        self.counter = self.counter + 1

        # Wait until the end of the day (so we only trade once per day)
        self.await_market_to_close()

    def on_abrupt_closing(self):
        # This is what we do when the program crashes
        self.sell_all()
