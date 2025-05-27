import os
import time
import threading
import requests
from flask import Flask
from dotenv import load_dotenv
from binance.client import Client

# Load .env variables
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

# Binance client
client = Client(api_key, api_secret)

# Settings
symbol = "BANANAUSDT"
take_profit_pct = 0.05  # 5%
check_interval = 300  # 5 minutes

# Flask App
app = Flask(__name__)

@app.route("/ping")
def ping():
    return "pong", 200

def run_server():
    app.run(host="0.0.0.0", port=8080)

# Helper Functions
def get_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except:
        return None

def get_balance(asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return float(balance["free"]) if balance else 0
    except:
        return 0

def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except:
        pass

def sell_all_to_usdt():
    account = client.get_account()
    for bal in account["balances"]:
        asset = bal["asset"]
        free = float(bal["free"])
        if asset not in ["USDT", "BNB"] and free > 0.001:
            symbol = asset + "USDT"
            try:
                client.order_market_sell(symbol=symbol, quantity=round(free, 0))
                send_telegram(f"Sold {free} {asset} to USDT")
            except:
                continue

def buy_banana():
    usdt = get_balance("USDT")
    price = get_price("BANANAUSDT")
    if usdt > 0.001 and price:
        qty = round(usdt / price, 0)
        try:
            client.order_market_buy(symbol="BANANAUSDT", quantity=qty)
            send_telegram(f"Bought {qty} BANANA @ {price}")
            return price
        except:
            pass
    return None

def sell_banana_if_profit(buy_price):
    current_price = get_price("BANANAUSDT")
    if not current_price or not buy_price:
        return buy_price
    change = (current_price - buy_price) / buy_price
    if change >= take_profit_pct:
        qty = get_balance("BANANA")
        if qty > 0.001:
            try:
                client.order_market_sell(symbol="BANANAUSDT", quantity=round(qty, 0))
                send_telegram(f"Sold {qty} BANANA for profit at {current_price}")
                return None
            except:
                pass
    return buy_price

# Trading Logic
def run_bot():
    bought_price = None
    while True:
        try:
            sell_all_to_usdt()
            if not bought_price:
                bought_price = buy_banana()
            else:
                bought_price = sell_banana_if_profit(bought_price)
        except Exception as e:
            send_telegram(f"[ERROR] {e}")
        time.sleep(check_interval)

# Status notification every 5 mins
def keep_alive_notifier():
    while True:
        send_telegram("Logan bot is active & monitoring market...")
        time.sleep(check_interval)

# Start everything
if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    threading.Thread(target=keep_alive_notifier).start()
    run_bot()