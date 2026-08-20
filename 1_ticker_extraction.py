"""
:date: 2026-08-19
:author: Eduardo González Agüero

Extracts US tickers from Nasdaq-published database.
"""
import csv, requests, pandas as pd

URLS = ["https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
        "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"]

'Note: headers different'

rows = []

dummy = []
for url in URLS:
        r = requests.get(url)
        lines = r.text.splitlines()
        header = lines[0].split("|")
        header[0] = "Symbol" # In one of them (?) not 'Symbol' but 'ACT Symbol'
        rows = [row.split("|") for row in lines[1:-1]] # -1 not actual row, info on Last Creation Time
        df = pd.DataFrame(data=rows, columns=header)
        dummy.append(df)
result = pd.concat(dummy, join = 'inner')

cols = ", ".join(result.columns)

print(f"""
Each dataset has its own colums. After 'ACT Symbol' -> 'Symbol' remake, we are left
with the following common columns: {cols}. Where 'Symbol' and 'Security Name' are
straightforward. Others:

- Test Issue: Indicates whether or not the security is a test security.
Values: Y = yes, it is a test issue. N = no, it is not a test issue. We want to keep
N securities.

- Round Lot Size: Indicates the number of shares that make up a round lot for
the given security. Can't see relevance right now.

- ETF: Wether it is an ETF or not. Might want to keep this one

We are going to drop Round Lot Size, filter & remove Test Issue, keep ETF
""")

result = result[result["Test Issue"] == 'N'].drop(
        columns=['Test Issue', 'Round Lot Size']
        )
print(result.head(), f"\nShape: {result.shape}") # Not many Test Issues!

result.to_csv("csv/1_ticker_extraction_nasdaq.csv")