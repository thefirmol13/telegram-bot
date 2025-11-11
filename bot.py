import os
import logging
from flask import Flask, request, jsonify
import requests
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем токен бота из Secrets Replit
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("Токен бота не найден! Проверьте Secrets в Replit")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Создаем Flask приложение
app = Flask(__name__)

def send_message(chat_id, text):
    """Отправка сообщения через Telegram API"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, json=data)
        logger.info(f"Сообщение отправлено: {text}")
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return None


def get_weather(city="Москва"):
    """Получение погоды через OpenMeteo API для любого города"""
    try:
        # Сначала получаем координаты города через геокодинг
        geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru"
        geocoding_response = requests.get(geocoding_url)
        geocoding_data = geocoding_response.json()

        if 'results' in geocoding_data and len(geocoding_data['results']) > 0:
            result = geocoding_data['results'][0]
            latitude = result['latitude']
            longitude = result['longitude']
            city_name = result['name']  # Правильное название города
        else:
            return f"❌ Город '{city}' не найден"

        # Затем получаем погоду по координатам
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&timezone=auto"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        if 'current_weather' in weather_data:
            weather = weather_data['current_weather']
            temperature = weather['temperature']
            windspeed = weather['windspeed']
            weather_code = weather['weathercode']
            is_day = weather['is_day']
            time = weather['time']

            # Получаем дату и время
            from datetime import datetime
            dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
            date_str = dt.strftime("%A, %d %B %Y г.").replace("Monday", "понедельник").replace("Tuesday",
                                                                                               "вторник").replace(
                "Wednesday", "среда").replace("Thursday", "четверг").replace("Friday", "пятница").replace("Saturday",
                                                                                                          "суббота").replace(
                "Sunday", "воскресенье")
            time_str = dt.strftime("%H:%M:%S")

            # Описание погоды
            weather_descriptions = {
                0: "☀️ Ясно", 1: "🌤️ Преимущественно ясно", 2: "⛅️ Переменная облачность",
                3: "☁️ Пасмурно", 45: "🌫️ Туман", 48: "🌫️ Густой туман",
                51: "🌧️ Легкая морось", 53: "🌧️ Умеренная морось", 55: "🌧️ Сильная морось",
                61: "🌧️ Небольшой дождь", 63: "🌧️ Умеренный дождь", 65: "🌧️ Сильный дождь",
                80: "🌦️ Ливень", 95: "⛈️ Гроза"
            }

            weather_desc = weather_descriptions.get(weather_code, "❓ Неизвестно")
            time_of_day = "🌞 Сейчас день" if is_day == 1 else "🌙 Сейчас ночь"

            # Форматируем красивое сообщение
            weather_message = f"""
🌤️ ПОГОДА СЕЙЧАС
────────────────
🏙️ {city_name}
📅 {date_str}
────────────────
🌡️ Температура: {temperature}°C
💨 Ветер: {windspeed} км/ч
📝 {weather_desc}
{time_of_day}
────────────────
🕐 Данные на: {time_str}
            """.strip()

            return weather_message
        else:
            return "❌ Не удалось получить данные о погоде"

    except Exception as e:
        logger.error(f"Ошибка получения погоды: {e}")
        return "❌ Ошибка при получении погоды"



def get_exchange_rates():
    """Получение курсов валют через ЦБ РФ API"""
    try:
        # API ЦБ РФ для текущих курсов
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url)
        data = response.json()

        if 'Valute' in data:
            usd = data['Valute']['USD']
            eur = data['Valute']['EUR']

            usd_rate = round(usd['Value'], 2)
            eur_rate = round(eur['Value'], 2)

            usd_change = round(usd['Value'] - usd['Previous'], 2)
            eur_change = round(eur['Value'] - eur['Previous'], 2)

            # Форматируем изменения (↑ или ↓)
            usd_symbol = "📈" if usd_change > 0 else "📉" if usd_change < 0 else "➡️"
            eur_symbol = "📈" if eur_change > 0 else "📉" if eur_change < 0 else "➡️"

            usd_change_str = f"+{usd_change}" if usd_change > 0 else str(usd_change)
            eur_change_str = f"+{eur_change}" if eur_change > 0 else str(eur_change)

            exchange_message = f"""
💱 КУРС ВАЛЮТ ЦБ РФ
────────────────
🇺🇸 USD: {usd_rate} ₽ {usd_symbol} {usd_change_str}
🇪🇺 EUR: {eur_rate} ₽ {eur_symbol} {eur_change_str}
────────────────
🕐 Данные на: {datetime.now().strftime('%H:%M:%S')}
            """.strip()

            return exchange_message
        else:
            return "❌ Не удалось получить курсы валют"

    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")
        return "❌ Ошибка при получении курсов валют"


def get_stock_price(ticker):
    """Получение цены акции по тикеру с MOEX"""
    try:
        # Приводим тикер к верхнему регистру
        ticker = ticker.upper()

        # API MOEX для конкретной акции
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        response = requests.get(url)
        data = response.json()

        if 'securities' in data and 'data' in data['securities']:
            # Получаем информацию об акции
            security_data = data['securities']['data'][0]
            stock_name = security_data[2]  # Название акции

            # Получаем текущую цену из marketdata
            if 'marketdata' in data and 'data' in data['marketdata']:
                market_data = data['marketdata']['data'][0]
                current_price = market_data[12]  # LAST - последняя цена
                change = market_data[13]  # CHANGE - изменение
                change_percent = market_data[14]  # CHANGE % - изменение в %

                if current_price:
                    # Форматируем изменение
                    change_symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    change_str = f"+{change:.2f}" if change > 0 else f"{change:.2f}"
                    change_percent_str = f"+{change_percent:.2f}%" if change_percent > 0 else f"{change_percent:.2f}%"

                    stock_message = f"""
📈 АКЦИЯ MOEX
────────────────
🏢 {stock_name} ({ticker})
💰 Цена: {current_price} ₽
{change_symbol} Изменение: {change_str} ({change_percent_str})
────────────────
🕐 Данные на: {datetime.now().strftime('%H:%M:%S')}
                    """.strip()

                    return stock_message
                else:
                    return f"❌ Для акции {ticker} нет данных о цене"
            else:
                return f"❌ Нет рыночных данных для акции {ticker}"
        else:
            return f"❌ Акция с тикером '{ticker}' не найдена"

    except Exception as e:
        logger.error(f"Ошибка получения акции {ticker}: {e}")
        return f"❌ Ошибка при получении данных акции {ticker}"


@app.route('/')
def home():
    return "🚀 Бот работает! Используйте /start в Telegram"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхуков от Telegram"""
    try:
        # Получаем данные от Telegram
        update = request.get_json()
        logger.info(f"Получено обновление: {update}")

        # Извлекаем информацию о сообщении
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text', '')

            # Обрабатываем команды
            if text == '/start':
                send_message(chat_id,
                    'Привет! Я твой бот! 🚀\n'
                    'Доступные команды:\n'
                    '/weather [город] - погода\n'
                    '/exchange - курс валют\n'
                    '/stock [тикер] - акция MOEX\n'
                    '/help - помощь'
                )
            elif text == '/help':
                send_message(chat_id,
                    'Помощь:\n'
                    '/weather [город] - погода в указанном городе\n'
                    '/exchange - курс валют ЦБ РФ\n'
                    '/stock [тикер] - акция MOEX\n'
                    'Примеры:\n'
                    '/weather Лондон\n'
                    '/stock SBER\n'
                    '/stock GAZP'
                )
            elif text == '/exchange':
                # Обрабатываем команду курсов валют
                exchange_text = get_exchange_rates()
                send_message(chat_id, exchange_text)
            elif text.startswith('/weather'):
                # Обработка команды погоды
                parts = text.split(' ')
                if len(parts) > 1:
                    city = parts[1]  # Город из команды
                    weather_info = get_weather(city)
                else:
                    weather_info = get_weather()  # По умолчанию Москва
                send_message(chat_id, weather_info)
            elif text.startswith('/stock'):
                # Обработка команды акций
                parts = text.split(' ')
                if len(parts) > 1:
                    ticker = parts[1]  # Тикер из команды
                    stock_text = get_stock_price(ticker)
                    send_message(chat_id, stock_text)
                else:
                    send_message(chat_id,
                        '📈 Использование: /stock [тикер]\n'
                        'Примеры:\n'
                        '/stock SBER\n'
                        '/stock GAZP\n' 
                        '/stock LKOH\n'
                        '/stock YNDX'
                    )
            elif text:
                send_message(chat_id, f'Вы сказали: "{text}"')

        return jsonify({"status": "ok"})

    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return jsonify({"status": "error"})




if __name__ == '__main__':
    print("=" * 50)
    print("🚀 БОТ ЗАПУСКАЕТСЯ НА REPLIT")
    print(f"✅ Токен загружен: {'ДА' if BOT_TOKEN else 'НЕТ'}")
    print("=" * 50)

    app.run(host='0.0.0.0', port=8080, debug=False)