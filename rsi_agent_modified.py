
from ib_insync import *
import pandas as pd
import ta
import schedule
import time
import datetime
import subprocess
import pytz

# ⏰ Market hours filter (New York time)
def is_market_open():
    eastern = pytz.timezone('US/Eastern')
    now = datetime.datetime.now(eastern)
    return now.weekday() < 5 and datetime.time(9, 30) <= now.time() <= datetime.time(16, 0)

# 🔔 macOS native desktop notification
def mac_notify(title, message):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "{title}"'
    ])

# 📡 Connect to IBKR TWS (TWS must be running)
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# 📝 Your stock watchlist
symbols = ['PG', 'KO', 'CL', 'TSM', 'NVDA']

# 🔎 RSI monitoring logic
def check_rsi():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] Running RSI scan...")

    for symbol in symbols:
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            bars = ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr='30 D',
                barSizeSetting='1 day',
                whatToShow='MIDPOINT',
                useRTH=True,
                formatDate=1
            )

            df = util.df(bars)
            if df.empty or len(df) < 9:
                print(f"⚠️ Not enough data for {symbol}")
                continue

            df.set_index('date', inplace=True)
            rsi = ta.momentum.RSIIndicator(close=df['close'], window=9).rsi()
            latest_rsi = rsi.iloc[-1]
            print(f"📊 {symbol}: RSI = {latest_rsi:.2f}", end='')

            if latest_rsi < 30:
                print(" ⏰ RSI below 30! Potential oversold condition.")
                mac_notify(f"RSI Alert for {symbol}", f"RSI is {latest_rsi:.2f} — potential entry point.")
            else:
                print(" → No alert.")

        except Exception as e:
            print(f"⚠️ Error fetching RSI for {symbol}: {e}")

# 🔁 Run immediately and every 30 mins during market hours
check_rsi()  # First run immediately

def run_if_open():
    if is_market_open():
        check_rsi()
    else:
        print(f"[{datetime.datetime.now().strftime('%H:%M')}] Market is closed. Skipping scan.")

schedule.every(30).minutes.do(run_if_open)

print("📈 RSI Agent started. Checking every 30 minutes during US market hours.")

while True:
    schedule.run_pending()
    time.sleep(10)
