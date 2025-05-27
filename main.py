import time
import requests
from datetime import datetime

TELEGRAM_BOT_TOKEN = "7333244671:AAGih9nJ7Unze9bmdB65odJrnEuSs9adnJw"
TELEGRAM_CHAT_ID = "6978133426"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Failed to send message:", e)

def run_bot():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        send_telegram_message(f"[{now}] Bot is still active")
        
        # Hapa ndio uweke logic ya kuuza coins zote kwenda USDT,
        # kisha ununue BANANA ikishuka bei, na uziuze zikishapanda 5%.
        print("Running bot logic...")

        time.sleep(300)  # Subiri dakika 5

if __name__ == "__main__":
    run_bot()