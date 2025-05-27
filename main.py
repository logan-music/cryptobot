import requests

# Telegram credentials
BOT_TOKEN = "7333244671:AAGih9nJ7Unze9bmdB65odJrnEuSs9adnJw"
CHAT_ID = "6978133426"

# Ujumbe wa test
message = "Test: Bot imetumwa kutoka Fly.io kwa mafanikio!"

# Tuma message
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": message}

response = requests.post(url, data=payload)

# Print status
if response.status_code == 200:
    print("Ujumbe umetumwa kwa mafanikio!")
else:
    print("Imeshindikana kutuma ujumbe:")
    print(response.text)
