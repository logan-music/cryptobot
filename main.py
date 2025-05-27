import os
import time
import requests
from binance.client import Client
from dotenv import load_dotenv
from flask import Flask

# Load environment variables
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(api_key, api_secret)
symbol_to_buy = "BANANAUSDT"
min_trade_value = 0.001

app = Flask(__name__)

@app.route("/")
def home():
    return "Logan Bot is alive"

def get_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except:
        return None

def get_balance(asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return float(balance["free"]) if balance else 0.0
    except:
        return 0.0

def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def sell_all_assets_to_usdt():
    account_info = client.get_account()
    for asset in account_info["balances"]:
        free = float(asset["free"])
        coin = asset["asset"]

        if coin in ["USDT", "BNB"] or free < 0.0001:
            continue

        symbol = coin + "USDT"
        price = get_price(symbol)
        if not price:
            continue

        total_value = free * price
        if total_value > min_trade_value:
            try:
                quantity = int(free)
                client.order_market_sell(symbol=symbol, quantity=quantity)
                send_telegram(f"Sold {quantity} {coin} to USDT")
            except Exception as e:
                print(f"Failed to sell {coin}: {e}")

def buy_banana():
    usdt = get_balance("USDT")
    price = get_price(symbol_to_buy)
    if usdt > min_trade_value and price:
        quantity = round(usdt / price, 0)
        if quantity > 0:
            try:
                client.order_market_buy(symbol=symbol_to_buy, quantity=quantity)
                send_telegram(f"Bought {quantity} BANANA @ {price}")
            except Exception as e:
                print(f"Failed to buy BANANA: {e}")

def run_bot_loop():
    while True:
        sell_all_assets_to_usdt()
        buy_banana()
        send_telegram("Bot still running... (heartbeat)")
        time.sleep(300)  # Dakika 5

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_bot_loop).start()
    app.run(host="0.0.0.0", port=8080)