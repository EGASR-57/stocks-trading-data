"""
:date: 2026-09-01
:author: Eduardo González Agüero

Extracts US tickers from yfinance database.
"""

import logging

import yfinance as yf
import pandas as pd

# yfinance logs the 404 for unknown symbols instead of raising it, so quieten it.
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

d = pd.read_csv('csv/ftp_tickers.csv')
d = d.query('COUNTRY == "USA"')
test = d['#SYM'].iloc[:100].to_list()

# -- We need decent code to detect those for which we may have info
# -- we are using yfinance because in machine Bet we haven't TWS connection

ticks = yf.Tickers(test)
CATCH_ERROR = {'trailingPegRatio': None} # Determined experimentally :)
TEST = False
# print(ticks.tickers) # Dictionary symbol (str): Ticker (object)

if TEST:
    yexists = []
    yfails = []
    for i in ticks.tickers:
        ticker = ticks.tickers[i]
        info = ticker.info
        if info == CATCH_ERROR:
                yfails.append(i)
        else:
            yexists.append(i)

    print(f"Total tickers: {len(test)}; {len(yexists)} exist in the universe of tickers of yfinance, {len(yfails)} don't")
else:
    p = pd.read_csv('csv/ftp_tickers.csv')
    p['YF'] = None
    print(p.head())
    # Read subset of YF that are not T/F and query the API, update result as indicated
    # Do it in batches of countries.