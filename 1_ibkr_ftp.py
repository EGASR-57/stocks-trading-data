"""
'ftp://shortstock: @ftp2.interactivebrokers.com/'
"""
from urllib.request import urlopen
import concurrent.futures as conc
import pandas as pd

url = 'ftp://shortstock: @ftp2.interactivebrokers.com/'
# We are going to query the list of shortable stocks published by IBKR
data = urlopen(url).read().decode().splitlines()
files = [line.split()[-1] for line in data if line.strip().endswith('.txt')]

def scrape_file(file):
        url_ = url + file
        data = urlopen(url_).read().decode().splitlines()
        lines = [line.split("|")[:-1] + [file[:-4].upper()] for line in data]
        data = lines[1:-1]
        return data

mergd = []

with conc.ThreadPoolExecutor() as executor:
        results = executor.map(scrape_file, files)
        for result in results:
                if mergd == []:
                        print('Adding header')
                        result[0][-1] = 'COUNTRY'
                else:
                        result = result[1:] # Remove header, already incorporated in first iteration
                mergd += result
pd.DataFrame(data=mergd[1:], columns=mergd[0]).to_csv("csv/ftp_tickers.csv", index=False)
