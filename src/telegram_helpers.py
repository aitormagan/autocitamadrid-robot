import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
STAGE = os.environ.get('STAGE', None)


def send_text(chat_id, message):
    if STAGE == 'dev':
        message = f"⚠️ Este es un bot de pruebas y su funcionamiento no está garantizado 😥. Te recomendamos utilizar " \
                  f"la versión productiva que puedes encontrar en 👉 https://t.me/vacunacovidmadridbot \n\n{message}"
    send_text = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text, timeout=5)
    if response.status_code not in [200, 400, 403]:
        response.raise_for_status()
    return response.json()


