import requests

TOKEN = "7469070147:AAE-kAkVCCeZNVvkJ1nKz4SeSCuVfWLjzTE"
WEBHOOK_URL = "https://dekete.onrender.com/webhook_path"

resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
print(resp.json())