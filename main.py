import os
import time
import requests
import threading
from flask import Flask
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
check_interval = 300  # 5 mins
take_profit_pct = 0.05
price_drop_trigger = -0.02

app = Flask(__name__)

@app.route("/ping")
def ping():
    return "pong"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[Telegram ERROR]: {e}")

def get_price(symbol):
    try:
        price = client.get_symbol_ticker(symbol=symbol)["price"]
        return float(price)
    except:
        return None

def get_balance(asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return float(balance["free"])
    except:
        return 0

def sell_all_to_usdt():
    tickers = client.get_account()["balances"]
    for t in tickers:
        asset = t["asset"]
        if asset in ["USDT", "BNB"] or float(t["free"]) < 0.001:
            continue
        symbol = asset + "USDT"
        try:
            price = get_price(symbol)
            qty = float(t["free"])
            if price and qty >= 1:
                client.order_market_sell(symbol=symbol, quantity=int(qty))
                send_telegram(f"Sold {qty} {asset} to USDT")
        except Exception as e:
            print(f"[Sell Error] {symbol}: {e}")

def buy_banana():
    usdt = get_balance("USDT")
    price = get_price("BANANAUSDT")
    if usdt > 0.001 and price:
        qty = round(usdt / price, 0)
        if qty > 0:
            try:
                client.order_market_buy(symbol="BANANAUSDT", quantity=int(qty))
                send_telegram(f"Bought {qty} BANANA at {price}")
                return price
            except Exception as e:
                print(f"[Buy Error]: {e}")
    return None

def trade_bot():
    bought_price = None
    while True:
        send_telegram("Bot is active and running...")
        sell_all_to_usdt()
        current_price = get_price("BANANAUSDT")
        if not current_price:
            time.sleep(check_interval)
            continue

        balance = get_balance("BANANA")
        if balance < 1:
            bought_price = buy_banana()
        elif bought_price:
            change = (current_price - bought_price) / bought_price
            if change >= take_profit_pct:
                try:
                    client.order_market_sell(symbol="BANANAUSDT", quantity=int(balance))
                    send_telegram(f"Sold {int(balance)} BANANA at profit (+{round(change*100,2)}%)")
                    bought_price = None
                except Exception as e:
                    print(f"[Sell BANANA Error]: {e}")
            elif change <= price_drop_trigger:
                send_telegram("Price dropped, skipping buy...")
        time.sleep(check_interval)

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    trade_bot()