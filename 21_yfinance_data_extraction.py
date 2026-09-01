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


def is_quoted(info):
    """True if yfinance actually resolved the symbol.

    A symbol Yahoo doesn't know (a CUSIP such as 049323AB4, a delisted ticker)
    does NOT raise -- .info comes back as the single-key dict
    {'trailingPegRatio': None}. So detection is a content check, not a
    try/except: a real quote always carries 'symbol' and 'quoteType'.
    """
    return bool(info) and info.get('symbol') is not None \
        and info.get('quoteType') is not None


d = pd.read_csv('csv/ftp_tickers.csv')
d = d.query('COUNTRY == "USA"')
test = d['#SYM'].iloc[:100].to_list()

# -- We need decent code to detect those for which we may have info
# -- we are using yfinance because in machine Bet we haven't TWS connection

ticks = yf.Tickers(test)

quoted, unquoted = {}, []
for sym in test:
    try:
        info = ticks.tickers[sym].info
    except Exception as exc:            # network/rate-limit, not a bad symbol
        print(f'{sym}: lookup failed ({type(exc).__name__}: {exc})')
        unquoted.append(sym)
        continue

    if is_quoted(info):
        quoted[sym] = info
    else:
        unquoted.append(sym)

print(f'{len(quoted)} quoted, {len(unquoted)} not found')
print('not found:', unquoted)