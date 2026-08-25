import pandas as pd

import argparse
import sys
import threading
import queue

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

# Start with Spain for our test
df = pd.read_csv('csv/ftp_tickers.csv')
spain = df[df['COUNTRY'] == 'SPAIN']
symbols = spain['#SYM']
currencies = spain['CUR']
con = spain['CON']
sec_types = ['STK']*currencies.shape[0]
print(sec_types)

HOST = "127.0.0.1"
PORT = 7496
CLIENT_ID = 1

CONNECT_TIMEOUT = 15
REQ = 1

INFO_CODES = {2104, 2106, 2107, 2108, 2119, 2158}


class Info(EWrapper, EClient):
        def __init__(self):
                EClient.__init__(self, self)
                self.bars = []
                self.ready = threading.Event()
                self.result = queue.Queue()
                self.details = []

                def nextValidId(self, orderId:int):
                        self.ready.set()

                def contractDetails(self, reqId: int, contractDetails):
                        self.details.append(contractDetails)

                def contractDetailsEnd(self, reqId: int):
                        self.result.put(("done", None))

                def error(self, reqId, errorCode, errorString):
                        if errorCode in INFO_CODES:
                                print(f"tws: {errorString}", file=sys.stderr) #WASS
                                return
                        print(f"Error {errorCode}: {errorString}")
                        if reqId == REQ or errorCode in (502, 504, 1100):
                                self.result.put(("error", f"{errorCode}: {errorString}"))

def build_contract(conId: str):
        contract = Contract()
        contract.conId = conId
        return contract

def main():
        app = Info()
        app.connect(HOST, PORT, CLIENT_ID)
        thread = threading.Thread(target=app.run,daemon = True)
        thread.start()

        if not app.ready.wait(CONNECT_TIMEOUT):
                app.disconnect()
                print(f"No handshake from {HOST}:{PORT} within {CONNECT_TIMEOUT}s")

        contract = build_contract(conId=con.iloc[0])
        print(contract)
        app.reqContractDetails(reqId = REQ, contract = contract)

if __name__ == "__main__":
        main()