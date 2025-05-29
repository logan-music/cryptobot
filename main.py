import time
import requests
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException

# ==== API Keys (Wazi) ====
API_KEY = "t99fN1MWcaFytKHwEhec6PuW72Ptf4NpzExyl8c0U2PMaoYL7kDdop7IJPzyxLEb"
API_SECRET = "3anCWYwyAQDR5WPaapu8V3pcYYKrdqup0LPQfYGIdGCIEE0zPiXe7qLrTxhUFeM0"

# ==== Telegram Notification ====
BOT_TOKEN = "7501645118:AAHuL5xMbPY3WZXJVnidijR9gqoyyCS0BzY"
CHAT_ID = "6978133426"

# ==== Settings ====
TRADE_DELAY = 20  # sekunde kati ya trades
ERROR_DELAY = 300  # sekunde 300 = dakika 5
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
        result = client._request(
            method='GET',
            path='/sapi/v1/asset/get-funding-asset',
            signed=True
        )
        for asset in result:
            name = asset['asset']
            balance = float(asset['free'])
            if balance > 0:
                client._request(
                    method='POST',
                    path='/sapi/v1/asset/transfer',
                    signed=True,
                    data={
                        'type': 1,
                        'asset': name,
                        'amount': balance
                    }
                )
                notify(f"✅ Transferred {balance} {name} from Funding to Spot")
    except Exception as e:
        notify(f"⚠️ Transfer Error: {e}")
        time.sleep(ERROR_DELAY)

def sell_other_assets():
    try:
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
                        qty = free - (free % step_size)
                        qty = round(qty, 6)
                        if qty > 0:
                            client.order_market_sell(symbol=symbol, quantity=qty)
                            notify(f"✅ Sold {qty} {asset} (~${value:.5f})")
                            time.sleep(TRADE_DELAY)
                except Exception as e:
                    notify(f"❌ Sell Error on {symbol}: {e}")
                    time.sleep(ERROR_DELAY)
    except Exception as e:
        notify(f"❌ Sell Process Error: {e}")
        time.sleep(ERROR_DELAY)

def buy_cheap_coins():
    try:
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
                time.sleep(ERROR_DELAY)
    except Exception as e:
        notify(f"❌ Buy Process Error: {e}")
        time.sleep(ERROR_DELAY)

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
        time.sleep(ERROR_DELAY)
    time.sleep(TRADE_DELAY)
