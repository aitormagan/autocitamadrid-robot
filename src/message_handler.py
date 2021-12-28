from datetime import datetime
import pytz
import requests
from aws_lambda_powertools import Logger
from src import db, telegram_helpers


URL_AUTOCITA_CONFIG = "https://autocitavacuna.sanidadmadrid.org/ohcitacovid/assets/config/app-config.json"
logger = Logger(service="vacunacovidmadridbot")


def handle_update(update):
    message = update.get("message", {}).get("text", "")
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    name = user_info.get("first_name", "")

    if user_id:
        if message in ["/start", "/help"]:
            answers = [f"¡Hola {name}! Bienvenidx al sistema de notificación de vacunación."]
            answers.extend(handle_current_age())
            answers.append("🤔 ¿Vives en Madrid? ¿Usas mucho el metro? ¡Ahora tienes un nuevo "
                           "🤖 bot disponible! Con "
                           "[Metro Madrid - Tiempos de Espera](t.me/MetroMadridTiempoEsperaBot) "
                           "puedes obtener los tiempos de espera en cualquier 🚇 estación de metro "
                           "con simplemente 🗣️ decir el nombre o mandar tu 📍 ubicación.\n\n¡No "
                           "esperes más y pruébalo ya!")
        elif message in ["/subscribe"]:
            answers = ["Lo siento 😔, ya no admito más suscripciones. 🤔 Pero si quieres información de cuando puedes "
                       "recibir tu 💉 tercera dosis, puedes preguntar /currentage"]
        elif message in ["/cancel"]:
            answers = ["Toda tu información personal ya ha sido eliminada del sistema. ¡Gracias por tu confianza!"]
        else:
            answers = handle_current_age()

        update["answer"] = "\n".join(answers)
        logger.info(update)
        for answer in answers:
            telegram_helpers.send_text(user_id, answer)
    elif "my_chat_member" in update and "new_chat_member" in update["my_chat_member"] \
            and "status" in update["my_chat_member"]["new_chat_member"] \
            and update["my_chat_member"]["new_chat_member"]["status"] == "kicked":
        user_id = update["my_chat_member"]["from"]["id"]
        logger.info(f"User with id {user_id} stopped the bot")


def handle_current_age():
    try:
        max_year_of_birth = requests.get(URL_AUTOCITA_CONFIG, timeout=5).json()["dFin_Birthday"].split("/")[-1]
    except Exception:
        max_year_of_birth = 2016

    messages = [f"👉 Para 1️⃣ primeras citas, el sistema permite pedir cita a personas nacidas en {max_year_of_birth} o "
                f"antes."]

    thirds_dose_info = db.get_info_third_dose()
    madrid_tz = pytz.timezone('Europe/Madrid')
    now = datetime.now(madrid_tz)

    update_date = madrid_tz.localize(datetime.strptime(f"{thirds_dose_info['new_date_of_birth_date']} 07:00:00",
                                                       "%d/%m/%Y %H:%M:%S"))

    current_age_third_dose_key = "new_date_of_birth" if now > update_date else "previous_date_of_birth"
    current_age_third_dose = thirds_dose_info[current_age_third_dose_key]

    messages.append(f"👉 Para 3️⃣ terceras dosis, el sistema de autocita permite pedir cita a personas nacidas en "
                    f"{current_age_third_dose} o antes")

    if update_date > now:
        messages.append(f"¡🤗 Pero tengo buenas noticias! Desde el 📅 {thirds_dose_info['new_date_of_birth_date']} a "
                        f"las 07:00, las personas nacidas en {thirds_dose_info['new_date_of_birth']} podrán pedir "
                        f"cita para terceras dosis 👏")

    messages.append(f"¡Si cumples con algunos de estos criterios, no esperes más vacúnate! Puedes pedir cita 🕘 en " +
                    f"🔗 https://autocitavacuna.sanidadmadrid.org/ohcitacovid.")

    return messages
