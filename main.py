import os
import time
import requests
from flask import Flask
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(api_key, api_secret)
app = Flask(__name__)

symbol = "BANANAUSDT"
check_interval = 300
take_profit_pct = 0.05
stop_loss_pct = -0.05
last_buy_price = None

@app.route("/")
def home():
    return "Bot is running!"

def get_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception as e:
        print(f"[ERROR] get_price: {e}")
        return None

def get_balance(asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return float(balance["free"]) if balance else 0
    except Exception as e:
        print(f"[ERROR] get_balance: {e}")
        return 0

def buy_banana():
    usdt = get_balance("USDT")
    if usdt < 0.001:
        return None
    price = get_price(symbol)
    if not price:
        return None
    quantity = round(usdt / price, 0)
    if quantity > 0:
        try:
            client.order_market_buy(symbol=symbol, quantity=quantity)
            send_telegram(f"Bought {quantity} BANANA @ {price}")
            return price
        except Exception as e:
            print(f"[ERROR] buy_banana: {e}")
    return None

def sell_banana():
    quantity = get_balance("BANANA")
    if quantity < 1:
        return
    try:
        client.order_market_sell(symbol=symbol, quantity=int(quantity))
        send_telegram(f"Sold {quantity} BANANA")
    except Exception as e:
        print(f"[ERROR] sell_banana: {e}")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {"chat_id": telegram_chat_id, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")

def run_bot():
    global last_buy_price
    while True:
        try:
            current_price = get_price(symbol)
            banana_balance = get_balance("BANANA")

            if banana_balance < 1:
                last_buy_price = buy_banana()
            elif last_buy_price:
                change = (current_price - last_buy_price) / last_buy_price
                if change >= take_profit_pct or change <= stop_loss_pct:
                    sell_banana()
                    last_buy_price = None

            send_telegram("Bot still running...")
            time.sleep(check_interval)
        except Exception as e:
            print(f"[ERROR] run_bot loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))