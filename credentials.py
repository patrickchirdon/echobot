ALPACA_CONFIG = {
    # Put your own Alpaca key here:
    "API_KEY": "PKWCQBDHAEILDXYGG4ZO",
    # Put your own Alpaca secret here:
    "API_SECRET": "6vB4nZ1OpT9mA0HpizFHbsuJC2Rw5Ti88smxdp6z",
    # If you want to go live, you must change this
    "ENDPOINT": "https://paper-api.alpaca.markets",
}

KUCOIN_CONFIG = {
    "exchange_id": "kucoin",
    "password": "dajg34sakjg5290_oKG",
    "apiKey": "63c9f5c8476698000175f279",
    "secret": "bbecda6c-0b0e-445b-abf8-b01ae64fd538",
    # "margin": True,
    "sandbox": False,
}

INTERACTIVE_BROKERS_CONFIG = {
    "SOCKET_PORT": 7497,
    "CLIENT_ID": "999",
    "IP": "127.0.0.1"
}

# Optional - Only required for debt trading strategy
QUANDL_CONFIG = {"API_KEY": "sZBNDY6CYyVfFSwAbmeY"}


# Optional - Not Required
class AlphaVantageConfig:
    # Put your own Alpha Vantage key here:
    API_KEY = "30WM6G3P2TVGCIWL"
