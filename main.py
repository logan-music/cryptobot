from binance.client import Client

api_key = "iqHagbaiABKRNapKslzKZZHKq8ooYjTpOfypXnK0YQBFy2qXDMjd2HQ59m5RJNQa"
api_secret = "4SJOu1aRnTa1w8qZOb5MAw1PrJEpLsaeREvbJeE7O3ESOrDAX97a7g1SfDiaLm7F"

client = Client(api_key, api_secret)

try:
    account_info = client.get_account()
    print("✅ API Key is valid!")
except Exception as e:
    print("❌ Error:", e)
