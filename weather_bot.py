import os
import requests

def get_weather():
    CITY = 'Kyiv'
    OWM_API_KEY = os.environ['OWM_API_KEY']
    URL = f'https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OWM_API_KEY}&units=metric&lang=ru'

    response = requests.get(URL)
    data = response.json()
    temp = data['main']['temp']
    desc = data['weather'][0]['description']
    feels_like = data['main']['feels_like']
    humidity = data['main']['humidity']

    # Проверяем, есть ли дождь в описании
    rain_warning = ""
    if "дожд" in desc.lower():
        rain_warning = "\n☔️ Сегодня возможен дождь! Не забудь зонт."

    return f"""
🌍 Доброе утро! Погода в Киеве:
🌡 Температура: {round(temp)}°C
🌤 {desc.capitalize()}
🌡 Ощущается как: {round(feels_like)}°C
💧 Влажность: {humidity}%
{rain_warning}

Хорошего дня! ☀️
"""

def send_telegram_message(message):
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=payload)
    return response.json()

def main():
    try:
        weather_message = get_weather()
        result = send_telegram_message(weather_message)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
