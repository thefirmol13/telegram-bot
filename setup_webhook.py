import os
import requests

BOT_TOKEN = os.getenv('BOT_TOKEN')
REPLIT_DEV_DOMAIN = os.getenv('REPLIT_DEV_DOMAIN')

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not found!")
    exit(1)

if not REPLIT_DEV_DOMAIN:
    print("❌ REPLIT_DEV_DOMAIN not found!")
    exit(1)

# Webhook URL - Replit automatically maps to port 443 (HTTPS)
webhook_url = f"https://{REPLIT_DEV_DOMAIN}/webhook"

print("=" * 60)
print("🔧 НАСТРОЙКА ВЕБХУКА TELEGRAM")
print("=" * 60)
print(f"Webhook URL: {webhook_url}")

# Set webhook
api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
response = requests.post(api_url, json={"url": webhook_url})

if response.status_code == 200:
    result = response.json()
    if result.get('ok'):
        print("✅ Вебхук успешно установлен!")
        print(f"Описание: {result.get('description', 'N/A')}")
    else:
        print(f"❌ Ошибка: {result}")
else:
    print(f"❌ HTTP Error: {response.status_code}")
    print(response.text)

# Get webhook info
info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
info_response = requests.get(info_url)

if info_response.status_code == 200:
    info = info_response.json()
    if info.get('ok'):
        print("\n📋 ИНФОРМАЦИЯ О ВЕБХУКЕ:")
        webhook_info = info.get('result', {})
        print(f"URL: {webhook_info.get('url', 'N/A')}")
        print(f"Pending updates: {webhook_info.get('pending_update_count', 0)}")
        if webhook_info.get('last_error_message'):
            print(f"⚠️  Last error: {webhook_info.get('last_error_message')}")
print("=" * 60)
