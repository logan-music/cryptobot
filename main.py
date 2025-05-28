import time
import requests
from binance.client import Client

# ======= Plain Keys ========
API_KEY = "t99fN1MWcaFytKHwEhec6PuW72Ptf4NpzExyI8c0U2PMaoYL7kDdop7IJPzyxLEb"
API_SECRET = "3anCWYwyAQDR5WPaapu8V3pcYYKrdqup0LPQfYGldGClEE0zPiXe7qLrTxhUFeM0"
BOT_TOKEN = "7501645118:AAHuL5xMbPY3WZXJVnidijR9gqoyyCS0BzY"
CHAT_ID = "6978133426"

client = Client(API_KEY, API_SECRET)

# Telegram message function
def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# Auto-sell coins above $0.001
def auto_sell():
    balances = client.get_account()['balances']
    for coin in balances:
        asset = coin['asset']
        free = float(coin['free'])
        if asset in ["USDT", "BNB"] or free == 0:
            continue
        symbol = asset + "USDT"
        try:
            price = float(client.get_symbol_ticker(symbol=symbol)['price'])
            value = free * price
            if value >= 0.001:
                client.order_market_sell(symbol=symbol, quantity=free)
                send_telegram(f"🔻 Ameuza {free:.6f} {asset} (${value:.6f})")
        except:
            pass

# Buy cheap coins
def buy_cheap():
    usdt = float(client.get_asset_balance(asset="USDT")['free'])
    if usdt < 0.001:
        return

    targets = {
        "BANANAUSDT": 0.002,
        "PEPEUSDT": 0.000001,
        "VRAUSDT": 0.004,
        "FLOKIUSDT": 0.00001,
        "SHIBUSDT": 0.00001
    }

    for symbol, low_price in targets.items():
        try:
            price = float(client.get_symbol_ticker(symbol=symbol)['price'])
            if price <= low_price:
                qty = round(usdt / price, 2)
                if qty * price > 0.001:
                    client.order_market_buy(symbol=symbol, quantity=qty)
                    send_telegram(f"🟢 Amenunua {qty} {symbol.replace('USDT','')} kwa ${usdt}")
                    break  # Nunua coin moja tu kwa mzunguko huu
        except:
            continue

# Sell if profit is 5%+
def smart_profit_sell():
    balances = client.get_account()['balances']
    for coin in balances:
        asset = coin['asset']
        free = float(coin['free'])
        if asset == "USDT" or free == 0:
            continue
        symbol = asset + "USDT"
        try:
            trades = client.get_my_trades(symbol=symbol)
            if not trades:
                continue
            buy_price = float(trades[-1]['price'])
            price = float(client.get_symbol_ticker(symbol=symbol)['price'])
            if price >= buy_price * 1.05:
                client.order_market_sell(symbol=symbol, quantity=free)
                send_telegram(f"✅ Ameuza kwa faida {asset}: {free} @ ${price}")
        except:
            pass

# Main loop
last_ping = 0
while True:
    try:
        if time.time() - last_ping >= 600:
            send_telegram("💓 Bot inafanya kazi (heartbeat)")
            last_ping = time.time()

        auto_sell()
        smart_profit_sell()
        buy_cheap()
        time.sleep(20)
    except Exception as e:
        send_telegram(f"⚠️ Error kwenye bot: {str(e)}")
        time.sleep(60)
