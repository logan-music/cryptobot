import os
import time
import requests
from binance.client import Client
from dotenv import load_dotenv

# Load env vars
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(api_key, api_secret)

symbol = "SHIBUSDT"
take_profit_pct = 0.10
stop_loss_pct = -0.05
check_interval = 300  # seconds

def get_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception as e:
        print(f"[ERROR] Failed to fetch price: {e}")
        return None

def get_balance(asset):
    balance = client.get_asset_balance(asset=asset)
    return float(balance["free"]) if balance else 0

def buy_all_usdt(symbol):
    usdt = get_balance("USDT")
    if usdt < 0.001:
        return
    price = get_price(symbol)
    quantity = round(usdt / price, 0)
    if quantity > 0:
        try:
            order = client.order_market_buy(symbol=symbol, quantity=quantity)
            send_telegram(f"Bought {quantity} {symbol} @ {price}")
            return price
        except Exception as e:
            print(f"[ERROR] Failed to buy: {e}")
    return None

def sell_all(symbol):
    base = symbol.replace("USDT", "")
    quantity = get_balance(base)
    if quantity < 1:
        return
    try:
        client.order_market_sell(symbol=symbol, quantity=int(quantity))
        send_telegram(f"Sold {quantity} {base} (Take Profit / Stop Loss)")
    except Exception as e:
        print(f"[ERROR] Failed to sell: {e}")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] Telegram failed: {e}")

def run_bot():
    bought_price = None
    while True:
        current_price = get_price(symbol)
        if not current_price:
            time.sleep(60)
            continue

        coin_balance = get_balance(symbol.replace("USDT", ""))
        if coin_balance < 1:
            bought_price = buy_all_usdt(symbol)
        elif bought_price:
            change = (current_price - bought_price) / bought_price
            if change >= take_profit_pct or change <= stop_loss_pct:
                sell_all(symbol)
                bought_price = None
        time.sleep(check_interval)

if __name__ == "__main__":
    run_bot()
