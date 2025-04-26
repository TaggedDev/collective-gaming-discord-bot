import os
import requests
import dotenv

# Настройки прокси (замените на свои)
proxy_host = "194.87.230.79"  # IP или домен прокси
proxy_port = 42449                       # Порт SOCKS5 (обычно 1080)
proxy_username = "proxy_user"             # Если требуется аутентификация
proxy_password = "TcierPnNJdtTzGGH"             # Если требуется аутентификация


proxy_url = os.getenv('PROXY_URL')

# Прокси-словарь для requests
proxies = {
    'http': proxy_url,
    'https': proxy_url
}

# URL для проверки (можно заменить на любой другой)
test_url = "https://httpbin.org/ip"

try:
    # Отправляем запрос через прокси
    response = requests.get(test_url, proxies=proxies, timeout=10)
    
    # Проверяем ответ
    if response.status_code == 200:
        print("Прокси работает! Ответ сервера:")
        print(response.text)
    else:
        print(f"Прокси отвечает, но с ошибкой. Код статуса: {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"Ошибка подключения через прокси: {e}")