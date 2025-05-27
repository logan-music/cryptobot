import os
import time
import requests
from flask import Flask
from threading import Thread
from binance.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(api_key, api_secret)
symbol = "BANANAUSDT"
check_interval = 300  # 5 minutes
take_profit_pct = 0.05
price_drop_pct = -0.01

last_bought_price = None

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")

def get_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"[ERROR] get_price: {e}")
        return None

def get_balance(asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return float(balance["free"]) if balance else 0
    except:
        return 0

def sell_all_to_usdt():
    account = client.get_account()
    for asset in account['balances']:
        free = float(asset['free'])
        if free > 0.001 and asset['asset'] != "USDT":
            symbol = asset['asset'] + "USDT"
            try:
                client.order_market_sell(symbol=symbol, quantity=int(free))
                send_telegram(f"Sold {free} {asset['asset']} to USDT")
            except Exception as e:
                print(f"[ERROR] sell_all_to_usdt: {e}")

def buy_banana():
    usdt = get_balance("USDT")
    price = get_price(symbol)
    if usdt >= 0.001 and price:
        quantity = round(usdt / price, 0)
        if quantity > 0:
            try:
                order = client.order_market_buy(symbol=symbol, quantity=quantity)
                send_telegram(f"Bought {quantity} BANANA at {price}")
                return price
            except Exception as e:
                print(f"[ERROR] buy_banana: {e}")
    return None

def sell_banana():
    banana = get_balance("BANANA")
    if banana >= 1:
        try:
            client.order_market_sell(symbol=symbol, quantity=int(banana))
            send_telegram(f"Sold {int(banana)} BANANA for profit")
        except Exception as e:
            print(f"[ERROR] sell_banana: {e}")

def run_bot():
    global last_bought_price
    while True:
        send_telegram("Bot is alive and checking market...")
        price = get_price(symbol)
        balance = get_balance("BANANA")

        if balance < 1:
            sell_all_to_usdt()
            if last_bought_price and price:
                drop = (price - last_bought_price) / last_bought_price
                if drop <= price_drop_pct:
                    last_bought_price = buy_banana()
                else:
                    last_bought_price = price
            else:
                last_bought_price = buy_banana()
        else:
            if last_bought_price and price:
                change = (price - last_bought_price) / last_bought_price
                if change >= take_profit_pct:
                    sell_banana()
                    last_bought_price = None

        time.sleep(check_interval)

def start_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    Thread(target=run_bot).start()
    start_flask()