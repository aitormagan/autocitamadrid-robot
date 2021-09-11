import json
from src import message_handler


def handle_telegram_message(event, _):
    update = json.loads(event["body"])
    message_handler.handle_update(update)

    return {
        "statusCode": 200
    }
