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
ib.connect('127.0.0.1', 7497, clientId=1)  # Default port; adjust if needed

# 📝 Your stock watchlist
symbols = ['PG', 'KO', 'CL', 'TSM', 'NVDA']

# 🔎 RSI monitoring logic
def check_rsi():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] Running RSI scan...")

    for symbol in symbols:
        contract = Stock(symbol, 'SMART', 'USD')
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='14 D',
            barSizeSetting='1 day',
            whatToShow='MIDPOINT',
            useRTH=True,
            formatDate=1
        )

        df = util.df(bars)
        if df.empty or len(df) < 14:
            print(f"⚠️ Not enough data for {symbol}. Skipping.")
            continue

        df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        rsi_now = df['RSI'].iloc[-1]
        print(f"{symbol} RSI = {rsi_now:.2f}")

        if rsi_now < 30:
            msg = f"{symbol} RSI dropped below 30 ({rsi_now:.2f})"
            print(f"🚨 ALERT: {msg}")
            mac_notify("RSI Alert", msg)

# 🗓️ Schedule: every 30 minutes
schedule.every(30).minutes.do(check_rsi)

# ▶️ Initial log
print("📈 RSI Agent started. Watching:", ", ".join(symbols))
print("🔁 Checking every 30 minutes — only during US market hours.\n")

# ⏳ Main loop
while True:
    if is_market_open():
        schedule.run_pending()
    else:
        print("🌙 Market closed. Waiting...")
    time.sleep(60)
