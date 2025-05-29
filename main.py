import time
import requests
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import hmac, hashlib, urllib.parse

# ==== API Keys (Wazi) ====
API_KEY = "iqHagbaiABKRNapKslzKZZHKq8ooYjTpOfypXnK0YQBFy2qXDMjd2HQ59m5RJNQa"
API_SECRET = "4SJOu1aRnTa1w8qZOb5MAw1PrJEpLsaeREvbJeE7O3ESOrDAX97a7g1SfDiaLm7F"

# ==== Telegram Notification ====
BOT_TOKEN = "7501645118:AAHuL5xMbPY3WZXJVnidijR9gqoyyCS0BzY"
CHAT_ID = "6978133426"

# ==== Settings ====
TRADE_DELAY = 20         # sekunde kati ya trades
ERROR_DELAY = 300        # sekunde 300 = dakika 5
MIN_TRADE_USD = 0.001    # kiwango cha chini kuuza coin yoyote

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
        url = "https://api.binance.com/sapi/v1/asset/get-funding-asset"
        headers = {'X-MBX-APIKEY': API_KEY}
        params = {'timestamp': int(time.time() * 1000)}

        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        full_url = f"{url}?{query_string}&signature={signature}"

        response = requests.post(full_url, headers=headers)
        data = response.json()

        notify(f"📦 Binance Response: {data}")
        assets = data.get('data') or data.get('assets') or data

        if not isinstance(assets, list):
            notify("⚠️ Transfer Error: Unexpected data format from Binance.")
            time.sleep(600)
            return

        for asset in assets:
            name = asset['asset']
            balance = float(asset['free'])
            if balance > 0:
                transfer_url = "https://api.binance.com/sapi/v1/asset/transfer"
                transfer_params = {
                    'type': 1,
                    'asset': name,
                    'amount': balance,
                    'timestamp': int(time.time() * 1000)
                }
                transfer_query = urllib.parse.urlencode(transfer_params)
                transfer_signature = hmac.new(API_SECRET.encode(), transfer_query.encode(), hashlib.sha256).hexdigest()
                transfer_full_url = f"{transfer_url}?{transfer_query}&signature={transfer_signature}"

                transfer_response = requests.post(transfer_full_url, headers=headers)
                if transfer_response.status_code == 200:
                    notify(f"✅ Transferred {balance} {name} from Funding to Spot")
                else:
                    notify(f"❌ Transfer Failed: {transfer_response.text}")
        time.sleep(5)

    except Exception as e:
        notify(f"⚠️ Transfer Error: {e}")
        time.sleep(600)

def transfer_funding_to_spot():
    try:
        url = "https://api.binance.com/sapi/v1/asset/get-funding-asset"
        headers = {'X-MBX-APIKEY': API_KEY}
        params = {'timestamp': int(time.time() * 1000)}

        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        full_url = f"{url}?{query_string}&signature={signature}"

        response = requests.post(full_url, headers=headers)
        assets = response.json()

        notify(f"📦 Binance Response: {assets}")

        if not isinstance(assets, list):
            notify("⚠️ Transfer Error: Unexpected response format (not a list).")
            time.sleep(600)
            return

        for asset in assets:
            name = asset['asset']
            balance = float(asset['free'])
            if balance > 0:
                transfer_url = "https://api.binance.com/sapi/v1/asset/transfer"
                transfer_params = {
                    'type': 1,
                    'asset': name,
                    'amount': balance,
                    'timestamp': int(time.time() * 1000)
                }
                transfer_query = urllib.parse.urlencode(transfer_params)
                transfer_signature = hmac.new(API_SECRET.encode(), transfer_query.encode(), hashlib.sha256).hexdigest()
                transfer_full_url = f"{transfer_url}?{transfer_query}&signature={transfer_signature}"

                transfer_response = requests.post(transfer_full_url, headers=headers)
                if transfer_response.status_code == 200:
                    notify(f"✅ Transferred {balance} {name} from Funding to Spot")
                else:
                    notify(f"❌ Transfer Failed: {transfer_response.text}")
        time.sleep(5)

    except Exception as e:
        notify(f"⚠️ Transfer Error: {e}")
        time.sleep(600)

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
