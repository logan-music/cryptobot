import os
import time
import requests
from binance.client import Client
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(api_key, api_secret)
symbol_to_buy = "BANANAUSDT"
min_value_usd = 0.001  # Minimum USD value ya coin ili iuzwe

app = Flask(__name__)

@app.route("/ping")
def ping():
    return "Bot is alive"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] Telegram failed: {e}")

def sell_all_assets_to_usdt():
    account = client.get_account()
    balances = account["balances"]

    for balance in balances:
        asset = balance["asset"]
        free = float(balance["free"])
        if asset in ["USDT", "BNB"] or free == 0:
            continue

        try:
            symbol = asset + "USDT"
            price = float(client.get_symbol_ticker(symbol=symbol)["price"])
            value = free * price
            if value >= min_value_usd:
                quantity = int(free)
                client.order_market_sell(symbol=symbol, quantity=quantity)
                send_telegram(f"Sold {quantity} {asset} for USDT (≈ ${value:.4f})")
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Selling {asset}: {e}")

def buy_banana():
    try:
        usdt_balance = float(client.get_asset_balance(asset="USDT")["free"])
        if usdt_balance < min_value_usd:
            return
        price = float(client.get_symbol_ticker(symbol=symbol_to_buy)["price"])
        quantity = round(usdt_balance / price, 2)
        if quantity >= 1:
            client.order_market_buy(symbol=symbol_to_buy, quantity=quantity)
            send_telegram(f"Bought {quantity} BANANA at {price}")
    except Exception as e:
        print(f"[ERROR] Buying BANANA: {e}")

def run_bot_loop():
    while True:
        sell_all_assets_to_usdt()
        buy_banana()
        time.sleep(300)  # kila dakika 5

def start_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    Thread(target=start_flask).start()
    run_bot_loop()