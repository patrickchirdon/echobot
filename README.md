# echobot

see tradingbot.pptx for descriptions of the strategies

The easiest installation is to use the google colab link. Make sure to change the secret key and the api key in the credentials.py file.  save this to your google drive or a copy for yourself on colab. 

https://github.com/patrickchirdon/echobot/blob/main/crypto_custom_etf.ipynb


2023-04-08 18:31:02,020: root: INFO: BTC 17 Day Trend Following : Executing the on_bot_crash event method
2023-04-08 18:31:02,052: root: INFO: BTC 17 Day Trend Following : --- BTC 17 Day Trend Following Strategy Performance ---
2023-04-08 18:31:02,066: root: INFO: BTC 17 Day Trend Following : Total Return: 1,121.68%
2023-04-08 18:31:02,066: root: INFO: BTC 17 Day Trend Following : CAGR 88.75%
2023-04-08 18:31:02,066: root: INFO: BTC 17 Day Trend Following : Volatility 48.63%
2023-04-08 18:31:02,066: root: INFO: BTC 17 Day Trend Following : Sharpe 1.82
2023-04-08 18:31:02,066: root: INFO: BTC 17 Day Trend Following : Max Drawdown 63.50% on 2022-09-07
2023-04-08 18:31:02,066: root: INFO: BTC 17 Day Trend Following : RoMaD 139.77%
2023-04-08 18:31:02,066: root: INFO: BTC 17 Day Trend Following : --- BTC-USD Benchmark Performance ---
- BTC-USD: No data found for this date range, symbol may be delisted

![image](https://user-images.githubusercontent.com/39843493/233743453-2a14d1f2-5091-4725-83d7-2c9f8be02198.png)

![image](https://user-images.githubusercontent.com/39843493/233743476-77b036bf-23c1-435e-9cab-269533b2827a.png)

![image](https://user-images.githubusercontent.com/39843493/233743500-e029df33-9d40-411b-986a-cfee41119187.png)

![image](https://user-images.githubusercontent.com/39843493/233743513-94238aa6-2ace-4751-8a16-3fc2d94fcdf7.png)



Installation

https://www.youtube.com/watch?v=Qrnjq9Wu0Mo

1. install python   https://www.python.org/
2. install anaconda if you like   https://www.anaconda.com/

from command line--

3. install the packages in requirements.txt
pip install xyz
pip install quandl
pip install lumibot
pip install nltk

DOWNLOAD THE DATA FOLDER FROM HERE AND PUT IT IN THE SAME DIRECTORY AS THE STRATEGY.PY FILES
https://drive.google.com/drive/folders/1Q2-UU8S4WZ6MUNJNSnUC55oAsOp5sNHZ

-------------------------

4. set up an account with Alpaca, kucoin, interactive brokers, and alpha vantage

Just choose the brokers you want. Don't have to go with all of them.
https://app.alpaca.markets/login
https://www.kucoin.com/
https://www.interactivebrokers.com
https://www.alphavantage.co/

5. input your api key in the credentials.py file

--------------------------
optional:
create a trading station!!

6.Instructions:

![image](https://user-images.githubusercontent.com/39843493/229931221-d460bf5d-0097-457d-8046-5bdb1e1a9f78.png)


https://www.tradestation.com/?gclid=EAIaIQobChMI-tvPj5uR_gIVSBTUAR2dmQSIEAAYASAAEgK5F_D_BwE&gclsrc=aw.ds

![image](https://user-images.githubusercontent.com/39843493/229931005-59411fa3-5dee-491d-bb9d-81797b012e6f.png)

--------------------------
other python libraries of interest--
https://github.com/ranaroussi/quantstats
https://pypi.org/project/TA-Lib/

--------------------------
See the strategies in action!

https://www.youtube.com/watch?v=ou7JOCC4hBo

Example output--

run:
python example_stock_screener.py

![image](https://user-images.githubusercontent.com/39843493/229929939-8c818f00-5aa0-41e4-8b1c-2e3a842b7b8f.png)


