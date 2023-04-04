import os
from datetime import datetime

import pandas as pd
import requests
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.entities import TradingFee
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader


class CongressTrading(Strategy):
    # =====Overloading lifecycle methods=============

    parameters = {
        "type": "house",
        "days_to_hold": 28,
        "min_congress_purchase": 4,
        "stable_etf": "SGOV",
    }

    def initialize(self):
        # There is only one trading operation per day
        # No need to sleep between iterations
        self.sleeptime = "1D"
        self.last_data_download = None
        self.stock_tally = {
            "AAPL": {
                "count": 0,
                "occurances": [],
            }
        }
        self.minutes_before_closing = 1

    def before_starting_trading(self):
        if (
            self.last_data_download is None
            or (datetime.now() - self.last_data_download).days >= 1
        ):
            filename = "congress_trades.csv"

            # Load the data from the csv file (if it exists)
            if os.path.exists(filename):
                self.congress_trades = pd.read_csv(filename)
                self.congress_trades["Date"] = pd.to_datetime(
                    self.congress_trades["Date"]
                )
                self.congress_trades = self.congress_trades.set_index("Date")
            else:
                self.congress_trades = pd.DataFrame()

            token = "c16def7ea7ac1a20dec0a683b7a40b52b27a447c"

            url = "https://api.quiverquant.com/beta/live/housetrading"
            headers = {
                "accept": "application/json",
                "X-CSRFToken": "TyTJwjuEC7VV7mOqZ622haRaaUr0x0Ng4nrwSRFKQs7vdoBcJlK9qjAS69ghzhFu",
                "Authorization": f"Token {token}",
            }
            r = requests.get(url, headers=headers)
            response_json = r.json()
            df = pd.DataFrame(response_json)
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")

            # Check if we got any new data
            if len(df) > 0:
                if len(self.congress_trades) > 0:
                    # Sort the data by date
                    df = df.sort_index()
                    self.congress_trades = self.congress_trades.sort_index()

                    # Only keep the rows that are newer than the last row in the dataframe
                    df = df[df.index > self.congress_trades.index[-1]]

                    # Append the new data to the dataframe
                    self.congress_trades = self.congress_trades.append(df)
                else:
                    self.congress_trades = df

            # Save to csv
            self.congress_trades.to_csv(filename)

            self.last_data_download = datetime.now()

    def on_trading_iteration(self):
        days_to_hold = self.parameters["days_to_hold"]
        min_congress_purchase = self.parameters["min_congress_purchase"]
        stable_etf = self.parameters["stable_etf"]

        # Get the rows from self.congress_trades where the index is equal to the current date or days_to_hold days ago
        dt = self.get_datetime()
        congress_trades = self.congress_trades.loc[
            (self.congress_trades.index <= pd.Timestamp(dt.date()))
            & (
                self.congress_trades.index
                >= pd.Timestamp(dt.date() - pd.Timedelta(days_to_hold, unit="D"))
            )
        ]

        congress_purchases = congress_trades[
            congress_trades["Transaction"] == "Purchase"
        ]

        # Count the number of times each ticker appears in the congress_purchases dataframe
        congress_purchases_count = congress_purchases.groupby("Ticker").count()[
            "Transaction"
        ]

        # Filter out tickers that don't match the criteria
        stocks_to_hold_list = {}
        for ticker, count in congress_purchases_count.items():
            # Must have been purchased at least min_congress_purchase times
            if count < min_congress_purchase:
                continue

            # Exclude tickers that have a "." or "$" in them because they are not tradable
            if "." in ticker or "$" in ticker:
                continue

            # Check if the ticker still exists by getting the last price
            price = self.get_last_price(ticker)
            if price is None:
                # If the ticker does not exist then skip it
                continue

            stocks_to_hold_list[ticker] = count

        # Build portfolio weights based on the number of times each ticker has been purchased
        portfolio_weights = {}
        for ticker, count in stocks_to_hold_list.items():
            portfolio_weights[ticker] = count / sum(stocks_to_hold_list.values())

        # If there are no stocks to hold then only hold very stable ETF
        if len(portfolio_weights) == 0:
            portfolio_weights[stable_etf] = 1

        # Rebalance portfolio
        self.rebalance_portfolio(portfolio_weights)

    def rebalance_portfolio(self, portfolio_weights):
        """Rebalance the portfolio and create orders"""

        orders = []
        for symbol in portfolio_weights:
            # Get all of our variables from portfolio
            symbol = symbol
            weight = portfolio_weights[symbol]
            last_price = self.get_last_price(symbol)

            if last_price is None:
                continue

            # Get how many shares we already own
            # (including orders that haven't been executed yet)
            position = self.get_position(symbol)
            quantity = 0
            if position is not None:
                quantity = float(position.quantity)

            # Calculate how many shares we need to buy or sell
            shares_value = self.portfolio_value * weight
            self.log_message(
                f"The current portfolio value is {self.portfolio_value} and the weight needed is {weight}, so we should buy {shares_value}"
            )
            new_quantity = shares_value // last_price
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

            # Execute the order if necessary
            if side:
                order = self.create_order(symbol, abs(quantity_difference), side)
                orders.append(order)

        # Sell all positions that are not in the portfolio weights
        positions = self.get_positions()
        for position in positions:
            if (
                position.symbol not in portfolio_weights
                and position.symbol != self.quote_asset.symbol
            ):
                order = self.create_order(
                    position.asset,
                    position.quantity,
                    "sell",
                    quote=self.quote_asset,
                )
                orders.append(order)

        # Execute the sell orders first
        sell_orders = [order for order in orders if order.side == "sell"]
        self.submit_orders(sell_orders)

        self.sleep(5)

        # Execute the buy orders
        buy_orders = [order for order in orders if order.side == "buy"]
        self.submit_orders(buy_orders)


if __name__ == "__main__":
    is_live = False

    if is_live:
        ####
        # Run the strategy live
        ####

        from credentials import ALPACA_CONFIG

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG)
        strategy = CongressTrading(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Backtesting
        backtesting_start = datetime(2021, 5, 20)
        # backtesting_end = datetime(2022, 1, 1)
        backtesting_end = datetime(2023, 3, 15)

        trading_fee = TradingFee(percent_fee=0.0005, flat_fee=0.0)

        # Load results csv
        filename = "backtest_results.csv"
        if os.path.exists(filename):
            backtest_result_df = pd.read_csv(filename, index_col=0)
        else:
            backtest_result_df = pd.DataFrame()

        # Try different days to hold in increments of 10
        # for x in range(24, 45, 2):
        #     for y in range(4, 7, 1):
        # # Check if the backtest has already been run
        # if backtest_result_df.empty is False:
        #     if (backtest_result_df["days_to_hold"] == x).any() and (
        #         backtest_result_df["min_congress_purchase"] == y
        #     ).any():
        #         print(
        #             f"Skipping {x} days, {y} min purchases because it has already been run"
        #         )
        #         continue
        x = 28
        y = 4

        days_to_hold = x
        min_congress_purchase = y
        input_parameters = {
            "days_to_hold": days_to_hold,
            "min_congress_purchase": min_congress_purchase,
        }

        result = CongressTrading.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            buy_trading_fees=[trading_fee],
            sell_trading_fees=[trading_fee],
            parameters=input_parameters,
            name=f"CongressTrading {days_to_hold} Days, {min_congress_purchase} Min Purchases",
            # show_plot=False,
            # show_tearsheet=False,
        )

        # Add results to the input parameters
        result.update(input_parameters)

        # Add the results to the dataframe
        backtest_result_df = backtest_result_df.append(result, ignore_index=True)

        # Sort the dataframe by sharpe ratio

        # Save the results to a csv
        backtest_result_df.to_csv(filename)
