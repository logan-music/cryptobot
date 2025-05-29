from binance.client import Client

api_key = "t99fN1MWcaFytKHwEhec6PuW72Ptf4NpzExyl8c0U2PMaoYL7kDdop7IJPzyxLEb"
api_secret = "3anCWYwyAQDR5WPaapu8V3pcYYKrdqup0LPQfYGIdGCIEE0zPiXe7qLrTxhUFeM0"

client = Client(api_key, api_secret)

try:
    account_info = client.get_account()
    print("✅ API Key is valid!")
except Exception as e:
    print("❌ Error:", e)
