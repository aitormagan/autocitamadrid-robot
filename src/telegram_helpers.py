import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")


def send_text(chat_id, message):
    send_text = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chat_id}&parse_mode=MarkdownV2&text={message}'
    response = requests.get(send_text, timeout=5)
    if response.status_code not in [200, 400, 403]:
        response.raise_for_status()
    return response.json()


