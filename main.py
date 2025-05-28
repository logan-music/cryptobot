
import time
import requests
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException

# ==== API Keys (Wazi) ====
API_KEY = "A0N0ctDbfyMPC6lHdTCVkmnhNNeMZKcJKFO2dkOUaQRM7uJUu9uvA9ZnZzsjNnLh"
API_SECRET = "F8Ckh8rGsBh1zP4NOeAfVvGrgWx7RZoFQ4BE6oEkuVjAf1evU7xOPUBN6gHzgtnT"

# ==== Telegram Notification ====
BOT_TOKEN = "7098570087:AAGYTmSTvP3_3WeF8zrmYVY-vzyC1rJ8Djs"
CHAT_ID = "6753870733"

# ==== Settings ====
TRADE_DELAY = 20  # seconds
MIN_TRADE_USD = 0.001

# ==== Coins za kununua automatically ====
CHEAP_COINS = [
    'BANANAUSDT', 'SHIBUSDT', 'PEPEUSDT', 'FLOKIUSDT',
    'BONKUSDT', 'LUNCUSDT', 'SPELLUSDT', 'DENTUSDT',
    'SCUSDT', 'LEVEUSDT', 'SOLVUSDT', 'STOUSDT', 'TONUSDT'
]

# ==== Start Binance client ====
client = Client(API_KEY, API_SECRET)

def notify(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

def transfer_funding_to_spot():
    try:
        result = client.get_funding_wallet()
        for asset in result['assets']:
            name = asset['asset']
            balance = float(asset['free'])
            if balance > 0:
                client.transfer_funding_to_spot(asset=name, amount=balance)
                notify(f"✅ Transferred {balance} {name} from Funding to Spot")
    except Exception as e:
        notify(f"⚠️ Transfer Error: {e}")

def sell_other_assets():
    account = client.get_account()
    for balance in account['balances']:
        asset = balance['asset']
        free = float(balance['free'])
        if free > 0 and asset != 'USDT':
            symbol = asset + 'USDT'
            try:
                price = float(client.get_symbol_ticker(symbol=symbol)['price'])
                value = price * free
                if value >= MIN_TRADE_USD:
                    info = client.get_symbol_info(symbol)
                    step_size = float([f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['stepSize'])
                    qty = int(free / step_size) * step_size
                    qty = round(qty, 6)
                    client.order_market_sell(symbol=symbol, quantity=qty)
                    notify(f"✅ Sold {qty} {asset} (~${value:.5f})")
                    time.sleep(TRADE_DELAY)
            except Exception as e:
                notify(f"❌ Sell Error on {symbol}: {e}")

def buy_cheap_coins():
    usdt = float(client.get_asset_balance(asset='USDT')['free'])
    if usdt < MIN_TRADE_USD:
        notify("⚠️ Not enough USDT to buy cheap coins.")
        return
    portion = usdt / len(CHEAP_COINS)
    for symbol in CHEAP_COINS:
        try:
            price = float(client.get_symbol_ticker(symbol=symbol)['price'])
            qty = round(portion / price, 0)
            if qty > 0:
                client.order_market_buy(symbol=symbol, quantity=qty)
                notify(f"✅ Bought {qty} of {symbol}")
                time.sleep(TRADE_DELAY)
        except Exception as e:
            notify(f"❌ Buy Error on {symbol}: {e}")

# ==== Main Bot Loop ====
while True:
    try:
        notify("🤖 Bot Started Cycle...")
        transfer_funding_to_spot()
        sell_other_assets()
        buy_cheap_coins()
        notify("✅ Cycle Completed. Waiting for next...")
    except Exception as error:
        notify(f"❌ Unexpected Error: {error}")
    time.sleep(TRADE_DELAY)