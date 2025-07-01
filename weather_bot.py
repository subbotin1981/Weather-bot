import os
import requests
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_weather():
    """Получает данные о погоде и формирует сообщение с предупреждениями"""
    CITY = 'Kyiv'
    OWM_API_KEY = os.environ.get('OWM_API_KEY')
    
    if not OWM_API_KEY:
        raise ValueError("OWM_API_KEY не установлен в переменных окружения")
    
    try:
        # Получаем текущую погоду
        CURRENT_URL = f'https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OWM_API_KEY}&units=metric&lang=ru'
        current_response = requests.get(CURRENT_URL, timeout=10)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        # Проверяем успешность ответа
        if current_data.get('cod') != 200:
            raise Exception(f"Ошибка API OpenWeatherMap: {current_data.get('message', 'Неизвестная ошибка')}")
        
        temp = current_data['main']['temp']
        desc = current_data['weather'][0]['description']
        feels_like = current_data['main']['feels_like']
        humidity = current_data['main']['humidity']
        pressure_hpa = current_data['main']['pressure']
        pressure_mmHg = round(pressure_hpa * 0.75006)
        wind_speed = current_data['wind']['speed']
        lat = current_data['coord']['lat']
        lon = current_data['coord']['lon']
        
        # Получаем расширенные данные (UV-индекс)
        # Используем более современный API
        ONECALL_URL = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=ru'
        try:
            uv_response = requests.get(ONECALL_URL, timeout=10)
            if uv_response.status_code == 200:
                uv_data = uv_response.json()
                uvi = uv_data.get('current', {}).get('uvi', 0)
            else:
                # Fallback на старый API если новый не доступен
                OLD_ONECALL_URL = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric'
                uv_response = requests.get(OLD_ONECALL_URL, timeout=10)
                uv_response.raise_for_status()
                uv_data = uv_response.json()
                uvi = uv_data.get('current', {}).get('uvi', 0)
        except Exception as e:
            logger.warning(f"Не удалось получить UV-индекс: {e}")
            uvi = 0
        
        # Анализ угроз и рекомендаций
        warnings = []
        tips = []
        
        # Температурные предупреждения
        if temp >= 30:
            warnings.append("🌡 Жарко! Температура выше 30°C")
            tips.append("💧 Пей больше воды, избегай перегрева.")
        elif temp <= -10:
            warnings.append("🥶 Очень холодно! Температура ниже -10°C")
            tips.append("🧥 Одевайся теплее, берегись обморожения.")
        elif temp <= 0:
            warnings.append("❄️ Температура ниже нуля")
            tips.append("⚠️ Осторожно, возможен гололёд.")
        
        # Ветровые предупреждения
        if wind_speed >= 10:
            warnings.append(f"💨 Очень сильный ветер: {wind_speed} м/с")
            tips.append("⚠️ Избегай высоких объектов, будь осторожен на улице.")
        elif wind_speed >= 8:
            warnings.append(f"💨 Сильный ветер: {wind_speed} м/с")
            tips.append("⚠️ Будь осторожен на улице из-за ветра.")
        
        # Проверка на туман и плохую видимость
        fog_keywords = ['туман', 'дымка', 'смог', 'мгла']
        if any(word in desc.lower() for word in fog_keywords):
            warnings.append("🌫 Возможна плохая видимость (туман или смог)")
            tips.append("🚗 Будь осторожен при вождении, включи фары.")
        
        # Прогноз осадков на ближайшие часы
        try:
            FORECAST_URL = f'https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={OWM_API_KEY}&units=metric&lang=ru'
            forecast_response = requests.get(FORECAST_URL, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            rain_keywords = ['дожд', 'гроза', 'снег', 'ливень', 'град']
            rain_forecast = ""
            
            for item in forecast_data['list'][:6]:  # Ближайшие 18 часов
                weather_desc = item['weather'][0]['description'].lower()
                if any(word in weather_desc for word in rain_keywords):
                    time = item['dt_txt'].split(' ')[1][:5]
                    rain_forecast += f"• {time}: {weather_desc.capitalize()}\n"
            
            if rain_forecast:
                warnings.append("☔️ Возможны осадки:\n" + rain_forecast.strip())
                tips.append("🌂 Захвати зонт или дождевик на всякий случай.")
                
        except Exception as e:
            logger.warning(f"Не удалось получить прогноз осадков: {e}")
        
        # UV-индекс предупреждения
        if uvi >= 8:
            warnings.append(f"🔆 Очень высокий UV-индекс: {uvi}")
            tips.append("🧴 Обязательно используй солнцезащитный крем SPF 30+!")
        elif uvi >= 6:
            warnings.append(f"🔆 Высокий UV-индекс: {uvi}")
            tips.append("🧴 Используй солнцезащитный крем, особенно днём.")
        
        # Влажность
        if humidity >= 80:
            warnings.append(f"💧 Очень высокая влажность: {humidity}%")
            tips.append("😮‍💨 Может ощущаться духота, чаще проветривай помещения.")
        
        # Формируем блоки предупреждений и советов
        warning_block = ""
        if warnings:
            warning_block = "\n⚠️ <b>Предупреждения на сегодня:</b>\n" + "\n".join(warnings)
        
        tips_block = ""
        if tips:
            tips_block = "\n💡 <b>Полезные советы:</b>\n" + "\n".join(tips)
        
        # Время последнего обновления
        current_time = datetime.now().strftime("%H:%M")
        
        return f"""🌍 <b>Доброе утро! Погода в Киеве</b> ({current_time}):

🌡 <b>Температура:</b> {round(temp)}°C
🌤 <b>Описание:</b> {desc.capitalize()}
🌡 <b>Ощущается как:</b> {round(feels_like)}°C
💧 <b>Влажность:</b> {humidity}%
💨 <b>Ветер:</b> {wind_speed} м/с
📈 <b>Давление:</b> {pressure_mmHg} мм рт. ст.
🔆 <b>UV-индекс:</b> {uvi}
{warning_block}
{tips_block}

Хорошего дня! ☀️"""

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при получении данных о погоде: {e}")
        raise
    except KeyError as e:
        logger.error(f"Ошибка в структуре данных API: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении погоды: {e}")
        raise

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise ValueError("TELEGRAM_TOKEN или TELEGRAM_CHAT_ID не установлены в переменных окружения")
    
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if not result.get('ok'):
            raise Exception(f"Telegram API error: {result.get('description', 'Unknown error')}")
            
        logger.info("Сообщение успешно отправлено в Telegram")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при отправке в Telegram: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {e}")
        raise

def main():
    """Основная функция"""
    try:
        logger.info("Запуск получения данных о погоде...")
        weather_message = get_weather()
        
        logger.info("Отправка сообщения в Telegram...")
        result = send_telegram_message(weather_message)
        
        logger.info("Бот успешно отработал!")
        print("✅ Сообщение отправлено успешно!")
        
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        print(f"❌ Ошибка конфигурации: {e}")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        print(f"❌ Произошла ошибка: {e}")

if __name__ == "__main__":
    main()
