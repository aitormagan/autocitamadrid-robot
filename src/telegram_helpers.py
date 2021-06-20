import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")


def send_text(chat_id, message):
    send_text = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text, timeout=5)
    return response.json()
