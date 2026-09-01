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
print(ticks.tickers)
for t in ticks.tickers:
    print(ticks.tickers[t].info)

# -- We need decent code to detect those for which we may have info
# -- we are using yfinance because in machine Bet we haven't TWS