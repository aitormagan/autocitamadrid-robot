import os
from aws_lambda_powertools import Logger
from src import telegram_helpers
from src import db


UPDATE_CENTRES_TIME = int(os.environ.get("UPDATE_CENTRES_TIME", 300))
logger = Logger(service="vacunacovidmadridbot")


def handle_update(update):
    message = update.get("message", {}).get("text", "")
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")

    if user_id:
        answer = "¡Ahora puedes vacunarte sin cita previa 🎉! Aquí tienes la lista de centros donde puedes " \
             "hacerlo:\n\n➡️ *Wizink Center*: 24h\n➡️ *Wanda Metropolitano*: de 9.30 a 14:30 y de 15:30 " \
             "a 20:30 (salvo días de partido, el anterior y el posterior)\n➡️ *Hospital Enfermera Isabel " \
             "Zendal*: 24h\n➡️ [Puntos Centralizados de Vacunación](https://shorturl.at/itBER): de " \
             "9.30 a 18.00\n\n¡No esperes más, vacúnate 💉 ya!"

        if message in ["/start", "/help"]:
            answer = f"¡Hola {name}! Bienvenidx al sistema de notificación de vacunación.\n\n{answer}"

        update["answer"] = answer
        logger.info(update)
        telegram_helpers.send_text(user_id, answer)
    elif "my_chat_member" in update and "new_chat_member" in update["my_chat_member"] \
            and "status" in update["my_chat_member"]["new_chat_member"] \
            and update["my_chat_member"]["new_chat_member"]["status"] == "kicked":
        user_id = update["my_chat_member"]["from"]["id"]
        logger.info(f"User with id {user_id} stopped the bot")
        db.delete_notification(user_id)
