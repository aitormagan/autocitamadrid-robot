import json
from aws_lambda_powertools import Logger
from src import message_handler
from src import checker

logger = Logger(service="vacunacovidmadridbot")


def handle_telegram_message(event, _):
    try:
        update = json.loads(event["body"])
        logger.info(update)
        message_handler.handle_update(update)
    except Exception:
        logger.exception("Unhandled Exception")

    return {
        "statusCode": 200
    }


def handle_check(event, _):
    checker.main()
