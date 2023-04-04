import math
from decimal import Decimal

import pandas as pd
import praw
from credentials import ALPACA_CONFIG, CcxtConfig, InteractiveBrokersConfig
from lumibot.brokers.alpaca import Alpaca
from lumibot.brokers.ccxt import Ccxt
from lumibot.brokers.interactive_brokers import InteractiveBrokers
from lumibot.entities import Asset
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from praw.models import MoreComments
from symbol_sentiment import SymbolSentiment


class SocialMediaBot(Strategy):
    parameters = {
        "portfolio": [],
        "portfolio_drift_threshold": 0.05,
        "tradeable_portfolio_pct": 0.50,
        "sentiment_symbols": {},
        "post_limit": 20,
        "subreddit_name": "cryptocurrency",
    }

    def initialize(self):
        self.sleeptime = "1D"
        self.set_market("24/7")  # MUST be here for crypto to work

    def on_trading_iteration(self):
        tradeable_portfolio_pct = self.parameters["tradeable_portfolio_pct"]
        portfolio_drift_threshold = self.parameters["portfolio_drift_threshold"]
        subreddit_name = self.parameters["subreddit_name"]
        post_limit = self.parameters["post_limit"]

        sentiment_scores = self.get_sentiment_scores(subreddit_name, post_limit)
        self.calc_portfolio_weights(sentiment_scores)

        total_portfolio_drift = self.calc_portfolio_drift(tradeable_portfolio_pct)
        if total_portfolio_drift > portfolio_drift_threshold:
            self.log_message(
                f"The portfolio drift is {total_portfolio_drift*100:.2f}% which is greater than the threshold of {self.parameters['portfolio_drift_threshold']*100:.2f}%, so we need to rebalance"
            )
            self.rebalance_portfolio(tradeable_portfolio_pct)

    def calc_portfolio_weights(self, sentiment_scores, minimum_mentions=5):
        positive_score_coins = []
        positive_score_coins_sum = 0

        for coin in sentiment_scores:
            average_score = sentiment_scores[coin]["average_score"]
            if (
                average_score > 0
                and len(sentiment_scores[coin]["previous_scores"]) > minimum_mentions
            ):
                positive_score_coins.append(coin)
                positive_score_coins_sum += average_score

        portfolio = []

        # Set the weights of the coins that have a positive sentiment score
        for coin in positive_score_coins:
            average_score = sentiment_scores[coin]["average_score"]
            weight = average_score / positive_score_coins_sum
            self.log_message(
                f"{coin} - Score: {average_score} Weight: {weight*100:.2f}%"
            )
            portfolio.append(
                {
                    "symbol": coin,
                    "weight": weight,
                }
            )

        # Next set any other positions that we own to 0% weight (ie. sell them
        # so that we only have the coins that we have a sentiment for)
        positions = self.get_positions()
        for position in positions:
            if (
                position.symbol not in sentiment_scores
                and position.asset != self.quote_asset
            ):
                portfolio.append(
                    {
                        "symbol": position.asset.symbol,
                        "weight": 0,
                    }
                )

        self.parameters["portfolio"] = portfolio

        self.log_message(f"The new portfolio is: {portfolio}")

    def get_sentiment_scores(self, subreddit_name="cryptocurrency", post_limit=5):
        self.log_message(
            f"Started getting sentiment scores from subreddit '{subreddit_name}', post_limit = {post_limit}"
        )
        ss = SymbolSentiment(self.parameters["sentiment_symbols"])

        reddit = praw.Reddit(
            client_id="MMV3qc3UvwqUyF6ft3rP2Q",
            client_secret="RPZdIgvoxRO5SENMJC50R7LIBupluQ",
            user_agent="my user agent",
        )
        posts = reddit.subreddit(subreddit_name).hot(limit=post_limit)

        for post in posts:
            # Get Top level comments
            all_comments = post.comments
            for comment in all_comments:
                if not isinstance(comment, MoreComments):
                    result = ss.parse_text(comment.body)

        self.log_message("Done  getting sentiment scores from Reddit")
        self.log_message(f"The sentiment scores are: {ss.sentiment_scores}")

        return ss.sentiment_scores

    def calc_portfolio_drift(self, tradeable_portfolio_pct=1):
        total_portfolio_drift = Decimal(0)
        for asset in self.parameters["portfolio"]:
            # Get all of our variables from portfolio
            symbol = asset.get("symbol")
            asset_to_trade = Asset(symbol=symbol, asset_type="crypto")
            weight = asset.get("weight")
            quote = self.quote_asset
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
            position = self.get_position(asset_to_trade)
            if position is None:
                quantity = 0
            else:
                quantity = position.quantity

            # Calculate how many shares we need to buy or sell
            tradeable_portfolio_value = Decimal(
                self.portfolio_value * tradeable_portfolio_pct
            )

            current_shares_value = Decimal(last_price) * Decimal(quantity)
            current_weight = current_shares_value / tradeable_portfolio_value
            drift = Decimal(weight) - current_weight
            self.log_message(
                f"Current weight for {symbol} is {current_weight:.2f} and should be {weight:.2f}, so the drift is {drift*100:.2f}%"
            )

            total_portfolio_drift += abs(drift)

        self.log_message(f"Total portfolio drift is {total_portfolio_drift:.2f}")
        return float(total_portfolio_drift)

    def rebalance_portfolio(self, tradeable_portfolio_pct=1):
        """Rebalance the portfolio and create orders"""
        orders = []
        for asset in self.parameters["portfolio"]:
            # Get all of our variables from portfolio
            symbol = asset.get("symbol")
            asset_to_trade = Asset(symbol=symbol, asset_type="crypto")
            weight = asset.get("weight")
            quote = self.quote_asset
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
            position = self.get_position(asset_to_trade)
            if position is None:
                quantity = 0
            else:
                quantity = position.quantity

            # Calculate how many shares we need to buy or sell
            tradeable_portfolio_value = self.portfolio_value * tradeable_portfolio_pct
            shares_value = tradeable_portfolio_value * weight
            new_quantity = Decimal(str(shares_value / last_price))

            quantity_difference = new_quantity - quantity
            self.log_message(
                f"Currently own {quantity} shares of {symbol} but need {new_quantity} ({shares_value} {quote}), so the difference is {quantity_difference}"
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
                qty_trimmed = math.floor(qty * 100) / 100

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

        self.submit_orders(orders)


if __name__ == "__main__":
    # Used in both Lumibot and Discord
    sentiment_symbols = {
        "BTC": ["Bitcoin", "BTC"],
        "ETH": ["Ethereum", "ETH"],
        "SOL": ["Solana", "SOL"],
        "LTC": ["Litecoin", "LTC"],
        "MKR": ["MKR"],
        "UNI": ["Uniswap", "UNI"],
        "SHIB": ["SHIB"],
        "DOGE": ["Dogecoin", "DOGE"],
    }

    trader = Trader()

    # broker = Ccxt(CcxtConfig.KUCOIN_SANDBOX)
    broker = Alpaca(ALPACA_CONFIG)
    # broker = InteractiveBrokers(InteractiveBrokersConfig)

    strategy = SocialMediaBot(
        broker,
        # quote_asset=Asset(symbol="USDT", asset_type="crypto"),  # Use for Kucoin
        quote_asset=Asset(symbol="USD", asset_type="forex"),  # Use for Alpaca
        parameters={"sentiment_symbols": sentiment_symbols},
    )

    trader.add_strategy(strategy)
    strategies = trader.run_all()

