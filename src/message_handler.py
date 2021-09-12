import os
from datetime import datetime
from aws_lambda_powertools import Logger
from src import telegram_helpers
from src import db


logger = Logger(service="vacunacovidmadridbot")


def handle_update(update):
    message = update.get("message", {}).get("text", "")
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    name = user_info.get("first_name", "")

    if user_id:
        answer = "¡Ahora puedes vacunarte sin cita previa 🎉! Tienes más info ➡️ [aquí]" + \
                 "(https://www.comunidad.madrid/servicios/salud/vacunacion-frente-coronavirus-comunidad-madrid#plan-vacunacion)" + \
                 "\n\n¡No esperes más, vacúnate 💉 ya!"
        if message in ["/start", "/help"]:
            answer = f"¡Hola {name}! Bienvenidx al sistema de notificación de vacunación.\n\n{answer}"
        elif message in ["/cancel"]:
            answer = "Toda tu información personal ya ha sido eliminada del sistema. ¡Gracias por tu confianza!"
        elif message == "/currentage":
            answer = handle_current_age(update)

        update["answer"] = answer
        logger.info(update)
        telegram_helpers.send_text(user_id, answer)
    elif "my_chat_member" in update and "new_chat_member" in update["my_chat_member"] \
            and "status" in update["my_chat_member"]["new_chat_member"] \
            and update["my_chat_member"]["new_chat_member"]["status"] == "kicked":
        user_id = update["my_chat_member"]["from"]["id"]
        logger.info(f"User with id {user_id} stopped the bot")


def handle_current_age(_):
    min_years = db.get_min_years()
    max_year_of_birth = datetime.now().year - min_years
    message = f"El sistema de autocita permite pedir cita a personas nacidas en {max_year_of_birth} o antes. " \
              f"¡Si cumples con este criterio, no esperes más vacúnate! Ahora puedes hacerlo sin cita 🏃: di " \
              f"/mindate para obtener más información. También puedes pedir cita 🕘 en " \
              f"🔗 https://autocitavacuna.sanidadmadrid.org/ohcitacovid"

    return message
