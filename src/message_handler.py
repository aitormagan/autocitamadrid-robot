import os
from datetime import datetime
from aws_lambda_powertools import Logger
from src import telegram_helpers
from src import db


UPDATE_CENTRES_TIME = int(os.environ.get("UPDATE_CENTRES_TIME", 300))
logger = Logger(service="vacunacovidmadridbot")


def handle_update(update):
    message = update.get("message", {}).get("text", "")
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    name = user_info.get("first_name", "")

    if user_id:
        answer = "¡Ahora puedes vacunarte sin cita previa 🎉! Aquí tienes la lista de centros donde puedes " \
             "hacerlo:\n\n➡️ *Wizink Center*: 24h\n➡️ *Wanda Metropolitano*: de 9.30 a 14:30 y de 15:30 " \
             "a 20:30 (salvo días de partido, el anterior y el posterior)\n➡️ *Hospital Enfermera Isabel " \
             "Zendal*: 24h\n➡️ [Puntos Centralizados de Vacunación](https://shorturl.at/itBER): de " \
             "9.30 a 18.00\n\n¡No esperes más, vacúnate 💉 ya!"

        if message in ["/start", "/help"]:
            answer = f"¡Hola {name}! Bienvenidx al sistema de notificación de vacunación.\n\n{answer}"
        elif message in ["/cancel"]:
            answer = "Si quieres borrar ❌ tu suscripción sólo tienes que detener el bot. Para ello, accede al perfil " \
                     "y haz click en *Detener bot*."
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
        db.delete_notification(user_id)


def handle_current_age(_):
    min_years = db.get_min_years()
    max_year_of_birth = datetime.now().year - min_years
    message = f"El sistema de autocita permite pedir cita a personas nacidas en {max_year_of_birth} o antes. " \
              f"¡Si cumples con este criterio, no esperes más vacúnate! Ahora puedes hacerlo sin cita 🏃: di " \
              f"/mindate para obtener más información. También puedes pedir cita 🕘 en " \
              f"🔗 https://autocitavacuna.sanidadmadrid.org/ohcitacovid"

    return message
