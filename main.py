import time
from binance.client import Client
import requests

# ==== API Keys zako =====
API_KEY = "iqHagbaiABKRNapKslzKZZHKq8ooYjTpOfypXnK0YQBFy2qXDMjd2HQ59m5RJNQa"
API_SECRET = "4SJOu1aRnTa1w8qZOb5MAw1PrJEpLsaeREvbJeE7O3ESOrDAX97a7g1SfDiaLm7F"

# ==== Telegram Alert Info ====
BOT_TOKEN = "7501645118:AAHuL5xMbPY3WZXJVnidijR9gqoyyCS0BzY"
CHAT_ID = "6978133426"

client = Client(API_KEY, API_SECRET)

TRADE_DELAY = 30  # seconds between checks
MIN_TRADE_USD = 0.05
PROFIT_TARGET = 1.05  # 5% profit target

def notify(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

def get_price(symbol):
    return float(client.get_symbol_ticker(symbol=symbol)['price'])

def get_balance(asset):
    b = client.get_asset_balance(asset=asset)
    return float(b['free']) if b else 0

def get_step(symbol):
    info = client.get_symbol_info(symbol)
    return float([f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['stepSize'])

def round_qty(qty, step):
    precision = len(str(step).split('.')[-1])
    return round(qty - (qty % step), precision)

def trade_symbol(symbol, asset, buy_price_holder):
    usdt = get_balance('USDT')
    price = get_price(symbol)
    step = get_step(symbol)
    coin_balance = get_balance(asset)

    if coin_balance == 0 and usdt >= MIN_TRADE_USD:
        qty = round_qty(usdt / price, step)
        if qty > 0:
            client.order_market_buy(symbol=symbol, quantity=qty)
            buy_price_holder[asset] = price
            notify(f"✅ Bought {qty} {asset} at ${price}")
    elif coin_balance > 0:
        buy_price = buy_price_holder.get(asset)
        if buy_price and price >= buy_price * PROFIT_TARGET:
            qty = round_qty(coin_balance, step)
            if qty > 0:
                client.order_market_sell(symbol=symbol, quantity=qty)
                notify(f"✅ Sold {qty} {asset} at ${price} (Profit!)")
                buy_price_holder.pop(asset, None)

# ==== Start Message ====
notify("🤖 Bot Started and is now running...")

# ==== Main Bot Loop ====
buy_prices = {}

while True:
    try:
        trade_symbol("SHIBUSDT", "SHIB", buy_prices)
        trade_symbol("BANANAUSDT", "BANANAS31", buy_prices)
    except Exception as e:
        notify(f"❌ Error: {e}")
    time.sleep(TRADE_DELAY)