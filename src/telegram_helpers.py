import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")


def get_updates(offset=0):
    result = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}")
    result.raise_for_status()
    return result.json()


def send_text(chat_id, message):
    send_text = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text)
    return response.json()
