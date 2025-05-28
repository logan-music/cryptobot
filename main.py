import os
import time
import requests
from binance.client import Client

# Binance credentials
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Telegram credentials
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Connect to Binance
client = Client(API_KEY, API_SECRET)

# Function to send Telegram message
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Telegram error:", response.text)
    except Exception as e:
        print("Telegram exception:", e)

# Function to check wallet and sell coins above $0.001
def auto_sell():
    balances = client.get_account()['balances']
    for coin in balances:
        asset = coin['asset']
        free = float(coin['free'])
        if asset == "USDT" or free == 0:
            continue
        symbol = asset + "USDT"
        try:
            price = float(client.get_symbol_ticker(symbol=symbol)['price'])
            value = free * price
            if value >= 0.001:
                order = client.order_market_sell(symbol=symbol, quantity=free)
                send_telegram_message(f"Ameuza {free:.6f} {asset} kwa takriban ${value:.6f}")
        except Exception as e:
            pass  # Symbol might not exist or other error

# Function to buy BANANAUSDT when price drops
def buy_banana():
    symbol = "BANANAUSDT"
    try:
        price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        if price < 0.002:  # bei ndogo
            usdt_balance = float(client.get_asset_balance(asset='USDT')['free'])
            if usdt_balance > 0.001:
                amount = usdt_balance / price
                order = client.order_market_buy(symbol=symbol, quantity=round(amount, 2))
                send_telegram_message(f"Amenunua {round(amount, 2)} BANANA kwa ${usdt_balance}")
    except Exception as e:
        pass

# Heartbeat notification every 5 minutes
last_ping = 0

while True:
    try:
        current_time = time.time()
        if current_time - last_ping >= 300:  # every 5 minutes
            send_telegram_message("✅ Bot inaendelea kukimbia vizuri (heartbeat)")
            last_ping = current_time

        auto_sell()
        buy_banana()
        time.sleep(30)  # delay between loops
    except Exception as e:
        send_telegram_message(f"⛔ Error kwenye bot: {e}")
        time.sleep(60)