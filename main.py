import time
import requests
from binance.client import Client

# === BINANCE & TELEGRAM KEYS (PLAIN TEXT) ===
API_KEY = "t99fN1MWcaFytKHwEhec6PuW72Ptf4NpzExyI8c0U2PMaoYL7kDdop7IJPzyxLEb"
API_SECRET = "3anCWYwyAQDR5WPaapu8V3pcYYKrdqup0LPQfYGldGClEE0zPiXe7qLrTxhUFeM0"
BOT_TOKEN = "7501645118:AAHuL5xMbPY3WZXJVnidijR9gqoyyCS0BzY"
CHAT_ID = "6978133426"

# === BINANCE CLIENT ===
client = Client(API_KEY, API_SECRET)

# === SEND TELEGRAM MESSAGE ===
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

# === COINS ZA KUNUNUA NA THRESHOLDS ZAO ===
cheap_targets = [
    {"symbol": "PEPEUSDT", "buy_below": 0.0000015},
    {"symbol": "SHIBUSDT", "buy_below": 0.000003},
    {"symbol": "FLOKIUSDT", "buy_below": 0.0003},
    {"symbol": "BONKUSDT", "buy_below": 0.00003},
    {"symbol": "DOGEUSDT", "buy_below": 0.001},
    {"symbol": "AKITAUSDT", "buy_below": 0.0000004},
    {"symbol": "BABYDOGEUSDT", "buy_below": 0.0000000015}
]

# === GET STEP SIZE FOR SYMBOL ===
def get_step_size(symbol):
    info = client.get_symbol_info(symbol)
    for filt in info["filters"]:
        if filt["filterType"] == "LOT_SIZE":
            return float(filt["stepSize"])
    return 1  # fallback

# === AUTO SELL ALL COINS > $0.001 ===
def auto_sell():
    balances = client.get_account()["balances"]
    for coin in balances:
        asset = coin["asset"]
        free = float(coin["free"])
        if asset == "USDT" or free == 0:
            continue
        symbol = asset + "USDT"
        try:
            price = float(client.get_symbol_ticker(symbol=symbol)["price"])
            value = free * price
            if value >= 0.001:
                step = get_step_size(symbol)
                qty = round(free - (free % step), 6)
                if qty > 0:
                    client.order_market_sell(symbol=symbol, quantity=qty)
                    send_telegram(f"Ameuza {qty} {asset} kwa takriban ${value:.6f}")
        except:
            pass

# === LOGIC YA KUNUNUA COINS ===
def auto_buy():
    try:
        usdt_balance = float(client.get_asset_balance(asset="USDT")["free"])
        if usdt_balance < 0.001:
            return
        budget = usdt_balance / 3  # Nunua max coin 3
        for coin in cheap_targets:
            symbol = coin["symbol"]
            threshold = coin["buy_below"]
            try:
                price = float(client.get_symbol_ticker(symbol=symbol)["price"])
                if price < threshold:
                    step = get_step_size(symbol)
                    qty = round(budget / price, 6)
                    qty = qty - (qty % step)
                    if qty > 0:
                        client.order_market_buy(symbol=symbol, quantity=qty)
                        send_telegram(f"Amenunua {qty} {symbol.replace('USDT','')} kwa ${budget:.6f}")
                        break
            except:
                continue
    except Exception as e:
        print("Buy error:", e)

# === MAIN LOOP ===
last_ping = 0

while True:
    try:
        if time.time() - last_ping >= 7200:
            send_telegram("💓 Bot inafanya kazi")
            last_ping = time.time()

        auto_sell()
        auto_buy()
        time.sleep(20)

    except Exception as e:
        send_telegram(f"⛔ Error kwenye bot: {e}")
        time.sleep(60)