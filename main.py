import os
import time
import threading
import requests
from flask import Flask
from binance.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

# Binance client
client = Client(api_key, api_secret)

# Flask setup
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is alive"

def start_flask():
    app.run(host="0.0.0.0", port=8080)

# Telegram notification
def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[Telegram Error] {e}")

# Get current price
def get_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except:
        return None

# Get balance
def get_balance(asset):
    balance = client.get_asset_balance(asset=asset)
    return float(balance["free"]) if balance else 0

# Sell any coin with value > $0.001 to USDT
def sell_all_to_usdt():
    account = client.get_account()
    for balance in account['balances']:
        asset = balance['asset']
        free = float(balance['free'])
        if asset == "USDT" or free < 0.001:
            continue
        symbol = asset + "USDT"
        try:
            price = get_price(symbol)
            if not price:
                continue
            value = price * free
            if value > 0.001:
                client.order_market_sell(symbol=symbol, quantity=round(free, 2))
                send_telegram(f"Sold {round(free, 2)} {asset} for USDT")
        except:
            continue

# Buy BANANA if price dropped
def buy_banana_if_dipped(prev_price):
    usdt = get_balance("USDT")
    if usdt < 0.001:
        return prev_price

    current_price = get_price("BANANAUSDT")
    if current_price and prev_price and current_price < prev_price:
        qty = round(usdt / current_price, 2)
        if qty > 0:
            try:
                client.order_market_buy(symbol="BANANAUSDT", quantity=qty)
                send_telegram(f"Bought {qty} BANANA at ${current_price}")
                return current_price
            except Exception as e:
                print(f"[Buy Error] {e}")
    return prev_price if prev_price else current_price

# Sell BANANA if price increased 5%+
def sell_banana_if_profit(buy_price):
    balance = get_balance("BANANA")
    if balance < 0.001 or not buy_price:
        return buy_price

    current_price = get_price("BANANAUSDT")
    if current_price and ((current_price - buy_price) / buy_price) >= 0.05:
        try:
            client.order_market_sell(symbol="BANANAUSDT", quantity=round(balance, 2))
            send_telegram(f"Sold {round(balance,2)} BANANA at ${current_price} (Profit)")
            return None
        except Exception as e:
            print(f"[Sell Error] {e}")
    return buy_price

# Main bot loop
def run_bot():
    banana_buy_price = None
    while True:
        send_telegram("Bot is active")
        sell_all_to_usdt()
        banana_buy_price = buy_banana_if_dipped(banana_buy_price)
        banana_buy_price = sell_banana_if_profit(banana_buy_price)
        time.sleep(300)  # 5 minutes

# Start
if __name__ == "__main__":
    threading.Thread(target=start_flask).start()
    run_bot()