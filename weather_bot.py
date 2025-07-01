import os
import requests

def get_weather():
    CITY = 'Kyiv'
    OWM_API_KEY = os.environ['OWM_API_KEY']

    # Получаем текущую погоду
    CURRENT_URL = f'https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OWM_API_KEY}&units=metric&lang=ru'
    current_response = requests.get(CURRENT_URL).json()

    temp = current_response['main']['temp']
    desc = current_response['weather'][0]['description']
    feels_like = current_response['main']['feels_like']
    humidity = current_response['main']['humidity']
    pressure_hpa = current_response['main']['pressure']
    pressure_mmHg = round(pressure_hpa * 0.75006)
    wind_speed = current_response['wind']['speed']

    lat = current_response['coord']['lat']
    lon = current_response['coord']['lon']

    # Получаем UV-индекс
    UV_URL = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric'
    uv_response = requests.get(UV_URL).json()
    uvi = uv_response['current'].get('uvi', 0)

    # Анализ угроз
    warnings = []
    tips = []

    if temp >= 30:
        warnings.append("🌡 Жарко! Температура выше 30°C")
        tips.append("💧 Пей больше воды, избегай перегрева.")

    if wind_speed >= 8:
        warnings.append(f"💨 Сильный ветер: {wind_speed} м/с")
        tips.append("⚠️ Будь осторожен на улице из-за ветра.")

    fog_keywords = ['туман', 'дымка', 'смог']
    if any(word in desc.lower() for word in fog_keywords):
        warnings.append("🌫 Возможна плохая видимость (туман или смог)")

    # Прогноз осадков
    FORECAST_URL = f'https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={OWM_API_KEY}&units=metric&lang=ru'
    forecast_response = requests.get(FORECAST_URL).json()
    rain_keywords = ['дожд', 'гроза', 'снег', 'ливень']
    rain_forecast = ""
    for item in forecast_response['list'][:6]:
        weather_desc = item['weather'][0]['description'].lower()
        if any(word in weather_desc for word in rain_keywords):
            time = item['dt_txt'].split(' ')[1][:5]
            rain_forecast += f"• {time}: {weather_desc.capitalize()}\n"

    if rain_forecast:
        warnings.append("☔️ Возможны осадки:\n" + rain_forecast.strip())
        tips.append("🌂 Захвати зонт или дождевик на всякий случай.")

    if uvi >= 6:
        warnings.append(f"🔆 Высокий UV-индекс: {uvi}")
        tips.append("🧴 Используй солнцезащитный крем, особенно днём.")

    warning_block = ""
    if warnings:
        warning_block = "\n⚠️ <b>Предупреждения на сегодня:</b>\n" + "\n".join(warnings)

    tips_block = ""
    if tips:
        tips_block = "\n💡 <b>Полезные советы:</b>\n" + "\n".join(tips)

    return f"""
🌍 Доброе утро! Погода в Киеве:
🌡 Температура: {round(temp)}°C
🌤 {desc.capitalize()}
🌡 Ощущается как: {round(feels_like)}°C
💧 Влажность: {humidity}%
💨 Ветер: {wind_speed} м/с
📈 Давление: {pressure_mmHg} мм рт. ст.
🔆 UV-индекс: {uvi}
{warning_block}
{tips_block}

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
