import os
import time
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Load API keys from environment variables or hardcoded for now
api_key = "t99fN1MWcaFytKHwEhec6PuW72Ptf4NpzExyI8c0U2PMaoYL7kDdop7IJPzyxLEb"
api_secret = "3anCWYwyAQDR5WPaapu8V3pcYYKrdqup0LPQfYGldGClEE0zPiXe7qLrTxhUFeM0"
telegram_token = "7333244671:AAGih9nJ7Unze9bmdB65odJrnEuSs9adnJw"
telegram_chat_id = "6978133426"

# Settings
symbol = "BANANAUSDT"
take_profit_pct = 0.05  # 5% profit
check_interval = 300  # 5 minutes

client = Client(api_key, api_secret)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[Telegram Error] {e}")

def get_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception as e:
        print(f"[Price Error] {e}")
        return None

def get_balance(asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return float(balance["free"]) if balance else 0
    except Exception as e:
        print(f"[Balance Error] {e}")
        return 0

def sell_all_tokens_to_usdt():
    account_info = client.get_account()
    balances = account_info["balances"]
    for token in balances:
        asset = token["asset"]
        free = float(token["free"])
        if asset in ["USDT", "BNB"] or free < 0.001:
            continue
        try:
            pair = f"{asset}USDT"
            client.order_market_sell(symbol=pair, quantity=int(free))
            send_telegram(f"Sold all {free} {asset} to USDT")
        except BinanceAPIException as e:
            print(f"[Sell Error] {asset}: {e}")

def buy_banana_if_price_drops(reference_price):
    usdt = get_balance("USDT")
    if usdt < 0.001:
        return None

    current_price = get_price(symbol)
    if not current_price or current_price > reference_price:
        return None

    quantity = round(usdt / current_price, 0)
    if quantity >= 1:
        try:
            order = client.order_market_buy(symbol=symbol, quantity=quantity)
            send_telegram(f"Bought {quantity} BANANA at {current_price}")
            return current_price
        except Exception as e:
            print(f"[Buy Error] {e}")
    return None

def sell_banana_if_profit(buy_price):
    quantity = get_balance("BANANA")
    if quantity < 1:
        return False

    current_price = get_price(symbol)
    if not current_price:
        return False

    profit_pct = (current_price - buy_price) / buy_price
    if profit_pct >= take_profit_pct:
        try:
            client.order_market_sell(symbol=symbol, quantity=int(quantity))
            send_telegram(f"Sold {quantity} BANANA at {current_price} (Profit {round(profit_pct*100, 2)}%)")
            return True
        except Exception as e:
            print(f"[Sell Profit Error] {e}")
    return False

def run_bot():
    send_telegram("Bot is active and running every 5 minutes.")
    reference_price = get_price(symbol)
    buy_price = None

    while True:
        try:
            sell_all_tokens_to_usdt()

            if not buy_price:
                buy_price = buy_banana_if_price_drops(reference_price)
            else:
                sold = sell_banana_if_profit(buy_price)
                if sold:
                    buy_price = None
                    reference_price = get_price(symbol)

            send_telegram("Heartbeat: Bot is alive.")
        except Exception as e:
            send_telegram(f"[Bot Error] {e}")

        time.sleep(check_interval)

if __name__ == "__main__":
    run_bot()