import os
import requests
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# Telegram bot credentials
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Coin na target
SYMBOL = "PEPEUSDT"
PROFIT_THRESHOLD = Decimal("0.015")  # 1.5%
initial_price = None

headers = {
    "X-MBX-APIKEY": API_KEY
}

def get_current_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return Decimal(data['price'])
    except Exception as e:
        print(f"[ERROR] Failed to fetch price: {e}")
        return None

def log_action(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{now}] {message}"
    print(log)
    with open("report.log", "a") as f:
        f.write(log + "\n")

def calculate_daily_profit():
    if not os.path.exists("report.log"):
        return Decimal("0.0")
    total = Decimal("0.0")
    with open("report.log", "r") as f:
        for line in f.readlines():
            if "Sell signal" in line:
                parts = line.split("price up")
                if len(parts) > 1:
                    try:
                        percent = parts[1].replace("%", "").strip()
                        gain = Decimal(percent) / 100
                        total += gain
                    except:
                        pass
    return total

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR] Failed to send telegram message: {e}")

def check_and_notify():
    now = datetime.utcnow()
    east_africa_hour = (now.hour + 3) % 24
    if east_africa_hour == 4 and now.minute < 5:
        profit = calculate_daily_profit()
        msg = f"Logan Bot Daily Report:\nProfit last 24h from PEPE: +{profit:.2%}"
        send_telegram_message(msg)

def monitor_price():
    global initial_price
    current_price = get_current_price(SYMBOL)
    if current_price is None:
        return

    if initial_price is None:
        initial_price = current_price
        log_action(f"Initial price for {SYMBOL} set at {initial_price}")
        return

    change = (current_price - initial_price) / initial_price
    log_action(f"Current price: {current_price} | Change: {change:.4%}")

    if change >= PROFIT_THRESHOLD:
        log_action(f"[ACTION] Sell signal triggered! {SYMBOL} price up {change:.2%}")
        # You can add Binance SELL order logic here if you want

if __name__ == "__main__":
    monitor_price()
    check_and_notify()
