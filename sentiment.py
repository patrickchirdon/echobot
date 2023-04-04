import nltk
from nltk import tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download("vader_lexicon")
nltk.download("punkt")

# Turn it into a class we can reuse
class SymbolSentiment:
    def __init__(self, symbols):
        self.symbols = symbols
        self.sentiment_scores = {}

    def get_coin_mentions(self, text):
        symbols_mentioned = []

        text = text.lower()
        words = tokenize.word_tokenize(text)
        for symbol in self.symbols:
            synonyms = self.symbols[symbol]
            for synonym in synonyms:
                if synonym.lower() in words:
                    symbols_mentioned.append(symbol.lower())

        return symbols_mentioned

    def get_sentiment(self, text):
        sid = SentimentIntensityAnalyzer()
        ss = sid.polarity_scores(text)
        return ss

    def parse_text(self, text):
        mentions = self.get_coin_mentions(text)
        sentiment = self.get_sentiment(text)

        found = False
        for symbol in self.symbols:
            if symbol.lower() in mentions:
                if symbol not in self.sentiment_scores:
                    self.sentiment_scores[symbol] = {
                        "average_score": 0.0,
                        "previous_scores": [],
                    }
                self.sentiment_scores[symbol]["previous_scores"].append(
                    sentiment["compound"]
                )
                self.sentiment_scores[symbol]["average_score"] = sum(
                    self.sentiment_scores[symbol]["previous_scores"]
                ) / len(self.sentiment_scores[symbol]["previous_scores"])
                found = True

        return found
