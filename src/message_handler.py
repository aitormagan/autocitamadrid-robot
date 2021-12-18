import requests
from aws_lambda_powertools import Logger
from src import telegram_helpers


URL_AUTOCITA_CONFIG = "https://autocitavacuna.sanidadmadrid.org/ohcitacovid/assets/config/app-config.json"
YEAR_BOOSTER = 1966
logger = Logger(service="vacunacovidmadridbot")


def handle_update(update):
    message = update.get("message", {}).get("text", "")
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    name = user_info.get("first_name", "")

    if user_id:
        answers = ["🤔 ¿No te has vacunado aún? Ahora puedes vacunarte sin cita. Tienes más info ➡️ [aquí]" +
                   "(https://www.comunidad.madrid/servicios/salud/vacunacion-frente-coronavirus-comunidad-madrid)",
                   "Si por lo contrario quieres te notifique cuando puedas ponerte una dosis de recuerdo, "
                   "aún no estoy preparado para eso 😔.\n👉 A día de hoy, sólo pueden conseguir su tercera dosis "
                   f"los nacidos en {YEAR_BOOSTER} o antes."]

        if message in ["/start", "/help"]:
            answers = [f"¡Hola {name}! Bienvenidx al sistema de notificación de vacunación."] + answers
        elif message in ["/cancel"]:
            answers = ["Toda tu información personal ya ha sido eliminada del sistema. ¡Gracias por tu confianza!"]
        elif message == "/currentage":
            answers = handle_current_age(update)

        update["answer"] = "\n".join(answers)
        logger.info(update)
        for answer in answers:
            telegram_helpers.send_text(user_id, answer)

        telegram_helpers.send_text(user_id, "🤔 ¿Vives en Madrid? ¿Usas mucho el metro? ¡Ahora tienes un nuevo "
                                            "🤖 bot disponible! Con "
                                            "[Metro Madrid - Tiempos de Espera](t.me/MetroMadridTiempoEsperaBot) "
                                            "puedes obtener los tiempos de espera en cualquier 🚇 estación de metro "
                                            "con simplemente 🗣️ decir el nombre o mandar tu 📍 ubicación.\n\n¡No "
                                            "esperes más y pruébalo ya!")
    elif "my_chat_member" in update and "new_chat_member" in update["my_chat_member"] \
            and "status" in update["my_chat_member"]["new_chat_member"] \
            and update["my_chat_member"]["new_chat_member"]["status"] == "kicked":
        user_id = update["my_chat_member"]["from"]["id"]
        logger.info(f"User with id {user_id} stopped the bot")


def handle_current_age(_):
    max_year_of_birth = requests.get(URL_AUTOCITA_CONFIG).json()["dFin_Birthday"].split("/")[-1]
    messages = [f"👉 Para 1️⃣ primeras citas, el sistema permite pedir cita a personas nacidas en {max_year_of_birth} o "
                f"antes.",
                f"👉 Para 3️⃣ terceras dosis, el sistema de autocita permite pedir cita a personas nacidas en "
                f"{YEAR_BOOSTER} o antes",
                f"¡Si cumples con algunos de estos criterios, no esperes más vacúnate! Puedes pedir cita 🕘 en " +
                f"🔗 https://autocitavacuna.sanidadmadrid.org/ohcitacovid."]

    return messages
