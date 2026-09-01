"""
:date: 2026-09-01
:author: Eduardo González Agüero

Extracts US tickers from yfinance database.
"""

import yfinance as yf
import pandas as pd

d = pd.read_csv('csv/ftp_tickers.csv')
# print(d.head())
d = d.query('COUNTRY == "USA"')
# print(d.head())
test = d['#SYM'].iloc[:100].to_list()
# print(test)
ticks = yf.Tickers(test)

# -- We need decent code to detect those for which we may have info
# -- we are using yfinance because in machine Bet we haven't TWS connection

# for i in range(10):
#     print(ticks.tickers[test[i]].info)

# test[-1] registered; 0 is not. 
p = ticks.tickers[test[-1]].info
print(type(p))
print(p.keys())