from datetime import datetime, timedelta

import pandas as pd
import quandl
from credentials import ALPACA_CONFIG, QUANDL_CONFIG
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.entities import Asset
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

"""
Strategy Description

This strategy will buy the two assets in `self.portfolio` and adjust their
proportions based on the change in the Debt to GDP ratio in the USA. 
In a normal situation, where Debt to GDP is increasing less than the 
`debt_change_threshold`, then we will own the `normal_ratio` of the first asset,
and put the rest of our money in the second asset.
In an increasing debt situation, where Debt to GDP is increasing more than the 
`debt_change_threshold`, then we will own the `buy_sp_ratio` of the first asset,
and put the rest of our money in the second asset.
"""


class DebtTrading(Strategy):
    # =====Overloading lifecycle methods=============
    parameters = {
        "debt_change_threshold": 0.15,
        "normal_ratio": 0.6,
        "buy_sp_ratio": 1,
        "period": "1D",
    }

    def initialize(self):
        # There is only one trading operation per day
        # No need to sleep between iterations
        self.sleeptime = self.parameters["period"]

        self.portfolio = [
            {
                "symbol": "UPRO",  # 3x Leveraged SPY (Equity)
                "weight": self.parameters["normal_ratio"],
            },
            {
                "symbol": "SPY",  # 3x Leveraged TLT (Long Term Bond)
                "weight": 1 - self.parameters["normal_ratio"],
            },
        ]

        self.debt_to_gdp_chng_df = None
        self.last_updated_data = None

    def before_market_opens(self):
        self.update_data()

    def on_trading_iteration(self):
        debt_change_threshold = self.parameters["debt_change_threshold"]
        normal_ratio = self.parameters["normal_ratio"]
        buy_sp_ratio = self.parameters["buy_sp_ratio"]

        # If the target number of days (period) has passed, rebalance the portfolio
        self.update_data()

        # The date according to Lumibot (eg. when backtesting)
        curdate = self.get_datetime()
        findme = datetime(curdate.year, curdate.month, curdate.day)
        debt_change = self.debt_to_gdp_chng_df.loc[
            self.debt_to_gdp_chng_df.index == findme
        ]["Debt to GDP 300 Day Change"].values[0]
        self.log_message(f"Debt level: {debt_change}")

        # The debt ratio is increasing fast
        if debt_change > debt_change_threshold:
            self.log_message(f"Using the buy_sp_ratio: {buy_sp_ratio}")
            self.portfolio[0]["weight"] = buy_sp_ratio
            self.portfolio[1]["weight"] = 1 - buy_sp_ratio

        # The debt ratio is increasing less than our threshold
        else:
            self.log_message(f"Using the normal_ratio: {normal_ratio}")
            self.portfolio[0]["weight"] = normal_ratio
            self.portfolio[1]["weight"] = 1 - normal_ratio

        self.rebalance_portfolio()

        self.log_message("Sleeping until next trading day")

    # =============Helper methods====================

    def update_data(self):
        # Only update the data every hour so that our backtests are fast
        now = datetime.now()
        if (self.last_updated_data is None) or (
            self.last_updated_data < now - timedelta(hours=1)
        ):
            self.debt_to_gdp_chng_df = self.get_debt_to_gdp_chng()
            self.last_updated_data = datetime.now()

    def get_debt_to_gdp_chng(self):
        start = datetime(1900, 1, 1)
        end = datetime.now()

        # Get the debt to GDP ratio

        quandl.ApiConfig.api_key = QUANDL_CONFIG["API_KEY"]
        debt_to_gdp = quandl.get("FRED/GFDEGDQ188S")
        debt_to_gdp_daily = debt_to_gdp.resample("D").fillna(method="ffill")

        # Forward fill so that we have today's value
        all_days = pd.DataFrame(index=pd.date_range(start, end))
        all_days = pd.concat([all_days, debt_to_gdp_daily], axis=1).fillna(
            method="ffill"
        )

        # Get the 300 day moving average
        all_days["Debt to GDP 300 Day Change"] = (
            all_days["Value"] / all_days["Value"].shift(300)
        ) - 1
        all_days = all_days.dropna()

        return all_days

    def rebalance_portfolio(self):
        """Rebalance the portfolio and create orders"""
        orders = []
        for asset in self.portfolio:
            # Get all of our variables from portfolio
            symbol = asset.get("symbol")
            weight = asset.get("weight")
            asset = Asset(symbol, asset_type="stock")
            last_price = self.get_last_price(asset)

            # Get how many shares we already own (including orders that haven't been executed yet)
            quantity = self.get_asset_potential_total(symbol)
            if quantity:
                self.log_message(
                    "Asset %s shares value: %.2f$. %.2f$ per %d shares."
                    % (symbol, quantity * last_price, last_price, quantity)
                )

            # Calculate how many shares we need to buy or sell
            shares_value = self.portfolio_value * weight
            new_quantity = shares_value // last_price
            quantity_difference = new_quantity - quantity
            self.log_message(
                "Weighted %s shares value with %.2f%% weight: %.2f$. %.2f$ per %d shares."
                % (symbol, weight * 100, shares_value, last_price, new_quantity)
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

        self.submit_orders(orders)


if __name__ == "__main__":
    is_live = False

    if is_live:
        ####
        # Run the strategy live
        ####

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG)
        strategy = DebtTrading(broker=broker)
        trader.add_strategy(strategy)
        trader.run_all()

    else:
        ####
        # Backtest the strategy
        ####

        # Choose the time from and to which you want to backtest
        backtesting_start = datetime(2012, 1, 1)
        backtesting_end = datetime(2023, 1, 1)

        # Initialize the backtesting object
        print("Starting Backtest...")
        DebtTrading.backtest(
            YahooDataBacktesting, backtesting_start, backtesting_end, parameters={}
        )
