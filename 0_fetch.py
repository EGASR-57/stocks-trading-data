"""
This is the dummy Claude code that performs a basic task with the IBKR API.

'Fetch historical bars from TWS / IB Gateway and write them to CSV.'
"""

import argparse
import csv
import queue
import sys
import threading

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

# TWS paper 7497 / live 7496, Gateway paper 4002 / live 4001.
HOST = "127.0.0.1" # Local TWS set to -- "Allow connections from localhost only"
PORT = 7496 # Determined in TWS
CLIENT_ID = 1 # TWS accepts several simultaneous API connections -- apparently not relevant for historic data

SYMBOL = "SPY" # SPDR S&P 500 ETF Trust
SEC_TYPE = "STK" # Stock
EXCHANGE = "SMART" # ?
CURRENCY = "USD" # ...

# A bar is a summary of everything that traded during one fixed slice of time.
DURATION = "1 M" # M <= month
BAR_SIZE = "1 day" # We could have it in weeks (5 days)
WHAT_TO_SHOW = "TRADES" # Changes what the prices represent. TRADES = actual executions; MIDPOINT/BID/ASK. These have no volume, wap, barCount.
USE_RTH = 1 # Sets the bar's boundaries.1 = Regular hours. 0 = Extra hours; ie, pre-market trade.

REQ_ID = 1
CONNECT_TIMEOUT = 15 # How long to wait for the handshake to complete.
DATA_TIMEOUT = 60

# Codes TWS sends on the error channel that are informational, not failures.
# Allowlist that keeps script from mistaking TWS' routine status chatter for failure.
INFO_CODES = {2104, 2106, 2107, 2108, 2119, 2158}

# ---- | --------------------------------------------------
# 2104   Market data farm connection is OK
# 2106   HMDS (historical) data farm connection is OK
# 2107   HMDS farm inactive, but available on demand
# 2108   Market data farm inactive, but available on demand
# 2110   Market data farm is connecting
# 2158   Sec-def data farm connection is OK

OUT_PATH = f"csv/0_{SYMBOL}.csv"


# ##### LE ACTUAL CODE #####

class HistoryApp(EWrapper, EClient):
    """
    HistoryApp inherits from two classes that are the two halves of the API, split
    by direction of travel.
    MRO: HistoryApp -> EWrapper -> EClient -> object

    Direction          inbound     outbound   (TWS -> client / client -> TWS)

    Nature             interface   actual implementation
                       of defaults

    1. EClient - Outbound
    Owns the socket and everything that serializes onto it. Its 104 methods are the
    requests: 'connect', 'reqHistoricalData', 'disconnect'. Also owns run() loop.

    2. EWrapper - Inbound
    We define four functions in this code -- whose names shadow the names in wrapper.py --
    The API 'activates' all 96 defined methods, but only those written in the class
    are not discarded. We define here:
    - nextValidId
    - error
    - historicalData
    - historicalDataEnd

    The first two are unprompted, the last two are not *visibly* prompted, but the
    API prompts them from hour request reqHistoricalData.


    """
    def __init__(self):
        EClient.__init__(self, self)
        self.bars = []
        self.ready = threading.Event()
        # (kind, payload) — kind is "done" or "error".
        self.result = queue.Queue()

    def nextValidId(self, orderId: int):
        # First message after a successful handshake: the socket is usable now.
        self.ready.set()

    def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson=""):
        if errorCode in INFO_CODES:
            print(f"tws: {errorString}", file=sys.stderr)
            return
        print(f"error {errorCode}: {errorString}", file=sys.stderr)
        if reqId == REQ_ID or errorCode in (502, 504, 1100):
            self.result.put(("error", f"{errorCode}: {errorString}"))

    def historicalData(self, reqId: int, bar):
        self.bars.append(bar)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        self.result.put(("done", None))


def build_contract(symbol, sec_type, exchange, currency):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = currency
    return contract


def write_csv(path, bars):
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "open", "high", "low", "close", "volume", "wap", "barCount"]) # Header
        for bar in bars:
            writer.writerow(
                [bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume, bar.wap, bar.barCount]
            )


def main():

    app = HistoryApp()
    app.connect(HOST, PORT, CLIENT_ID)
    thread = threading.Thread(target=app.run, daemon=True)
    thread.start()

    if not app.ready.wait(CONNECT_TIMEOUT):
        app.disconnect()
        sys.exit(f"no handshake from {HOST}:{PORT} within {CONNECT_TIMEOUT}s")

    app.reqHistoricalData(
        REQ_ID,
        build_contract(SYMBOL, SEC_TYPE, EXCHANGE, CURRENCY),
        "", # endDateTime, empty means now
        DURATION,
        BAR_SIZE,
        WHAT_TO_SHOW,
        USE_RTH,
        1,  # formatDate: {1,2}; 1 = yyyymmdd hh:mm:ss; don't use 2.
        False,  # keepUpToDate: If True, may return unfinished real-time bars (doesn't apply, don't use)
        [],
    )

    try:
        kind, payload = app.result.get(timeout=DATA_TIMEOUT)
    except queue.Empty:
        app.disconnect()
        sys.exit(f"no data for {SYMBOL} within {DATA_TIMEOUT}s")

    app.disconnect()
    thread.join(timeout=5)

    if kind == "error":
        sys.exit(payload)

    write_csv(OUT_PATH, app.bars)
    print(f"{len(app.bars)} bars -> {OUT_PATH}")


if __name__ == "__main__":
    main()
