
import yfinance as yf
import pandas as pd
import time
import schedule
from ta.momentum import RSIIndicator
from datetime import datetime
import pytz
import subprocess

# Parameters
SYMBOLS = ['PG', 'KO', 'CL', 'TSM', 'NVDA']
RSI_PERIOD = 9
RSI_THRESHOLD = 30
CHECK_INTERVAL_MINUTES = 30
TIMEZONE = 'US/Eastern'

def is_market_open():
    now = datetime.now(pytz.timezone(TIMEZONE))
    return now.weekday() < 5 and 9 <= now.hour < 16  # Market open 9:30am to 4pm

def send_mac_notification(title, message):
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], check=True)
    except Exception as e:
        print(f"⚠️ Notification failed: {e}")

def check_rsi():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running RSI scan...")
    for symbol in SYMBOLS:
        try:
            data = yf.download(symbol, period="15d", interval="1d", auto_adjust=True, progress=False)
            if data is None or data.empty or 'Close' not in data.columns:
                print(f"⚠️ No data for {symbol}")
                continue

            close_series = data['Close'].squeeze()
            if not isinstance(close_series, pd.Series):
                print(f"⚠️ Unexpected data format for {symbol}")
                continue

            rsi = RSIIndicator(close=close_series, window=RSI_PERIOD).rsi()
            latest_rsi = rsi.iloc[-1]
            status = "🔔 ALERT: RSI < 30!" if latest_rsi < RSI_THRESHOLD else "✅ OK"
            message = f"{symbol} RSI({RSI_PERIOD}) = {latest_rsi:.2f} → {status}"
            print(message)
            send_mac_notification("RSI Agent", message)

        except Exception as e:
            print(f"⚠️ Error processing {symbol}: {e}")

print("📈 RSI Agent with macOS Notification started. Monitoring every 30 minutes during US market hours.")

# Run immediately at start
check_rsi()

# Schedule periodic checks
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(lambda: check_rsi() if is_market_open() else None)

# Main loop
while True:
    schedule.run_pending()
    time.sleep(60)
