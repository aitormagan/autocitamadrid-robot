import re
from datetime import datetime
from aws_lambda_powertools import Logger
from src import telegram_helpers
from src import db
from src.checker import get_min_years


logger = Logger(service="vacunacovidmadridbot")


def handle_update(update):
    message = update.get("message", {}).get("text", "")
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")

    if user_id:
        try:
            if message in ["/start", "/help"]:
                answer = handle_start(update)
            elif message == "/cancel":
                answer = handle_cancel(update)
            elif message == "/status":
                answer = handle_status(update)
            elif message == "/currentage":
                answer = handle_current_age(update)
            elif message == "/subscribe":
                answer = handle_subscribe(update)
            else:
                answer = handle_generic_message(update)
        except Exception:
            logger.exception("Unexpected error")
            answer = "Perdoname 🙏, pero ha ocurrido un error inesperado 🤷 que me impide responder a tu solicitud. " \
                     "¿Podrías volver a intentarlo pasados unos minutos? Gracias 😃"

        update["answer"] = answer
        logger.info(update)
        telegram_helpers.send_text(user_id, answer)


def handle_start(update):
    user_info = update.get("message", {}).get("from", {})
    name = user_info.get("first_name", "")
    return f"¡Hola {name}! Bienvenido al sistema de notificación de vacunación. Si quieres que te avise 🔔 cuando " \
           f"puedas pedir cita para vacunarte 💉 en la Comunidad de Madrid, simplemente indicame la edad que " \
           f"tienes o tu año de nacimiento!\n\nOtros comandos útiles:\n-/subscribe: 🔔 Crea una suscripción para " \
           f"cuando puedas pedir cita para vacunarte\n- /help: 🙋 Muestra esta ayuda\n- /status: " \
           f"ℹ️ Muestra si ya estás suscrito\n- /cancel: 🔕 Cancela la notificación registrada\n - /currentage: " \
           f"📆 Muestra la edad mínima con la que puedes pedir cita"


def handle_cancel(update):
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    db.delete_notification(user_id)
    return f"¡Vale {user_info.get('first_name')}! He borrado ❌ tus datos y ya no te notificaré. Si quieres volver " \
           f"a activar la suscripción, simplemente di /start"


def handle_status(update):
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    user_notification = db.get_user_notification(user_id)
    if user_notification:
        age = user_notification["age"]
        if not user_notification["notified"]:
            message = "¡Todo listo 👏! Ya tienes activas las notificaciones 🔔 para cuando el sistema de autocita " \
                      f"permita pedir cita a personas de {age} o más años. Si quieres cancelarla, simplemente " \
                      f"escribe /cancel."
        else:
            message = f"¡Vaya 🤔! Parece que ya te he notificado de que las personas de {age} o más años pueden " \
                      f"pedir cita. Si quieres puedes crear otra suscripción: simplemente, dime la edad que tienes " \
                      f"o tu año de nacimiento. ¡Estaré encantado de volver a notificarte! 📳"
    else:
        message = "Actualmente no tienes ninguna notificación registrada 😓. Si quieres que te notifique 🔔 cuando " \
                  "puedas pedir cita para vacunarte simplemente dime tu año de nacimiento o tu edad."

    return message


def handle_current_age(update):
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    min_years = get_min_years()
    message = f"El sistema de autocita permite pedir cita a personas con {min_years} años o más️. Si cumples con " \
              f"la edad, puedes ir a 🔗 https://autocitavacuna.sanidadmadrid.org/ohcitacovid para pedir tu cita"

    user_notification = db.get_user_notification(user_id)
    if not user_notification:
        message += "\n\n⚠️ Puedo notificarte 🔔 cuando el sistema de autocitación permita vacunar a gente con tu " \
                   "edad. Simplemente dime tu edad o tu año de nacimiento."

    return message


def handle_subscribe(update):
    user_info = update.get("message", {}).get("from", {})
    user_name = user_info.get('first_name')
    message = f"¡👌 Vale {user_name}! ¿Me dices tu edad o tu año de nacimiento?"

    return message


def handle_generic_message(update):
    user_info = update.get("message", {}).get("from", {})
    received_message = update.get("message", {}).get("text", "")
    user_id = user_info.get("id")
    user_name = user_info.get('first_name')
    age = get_age(received_message)

    if age is not None:
        min_years = get_min_years()

        if age >= min_years:
            message = "‼️ ¡Ey! Parece que el sistema ya te permite pedir cita. ¡Hazlo ya en 🔗 " \
                      "https://autocitavacuna.sanidadmadrid.org/ohcitacovid/!"
        else:
            user_notification = db.get_user_notification(user_id)
            db.save_notification(user_id, user_name, age)
            message = f"¡Genial {user_name} ✅! Te notificaré 🔔 en cuando el sistema de autocitación " \
                      f"de la Comunidad de Madrid permita pedir cita a gente con {age} años. Si quieres " \
                      f"cancelar la suscripción, simplemente escribe /cancel."

            if user_notification and user_notification["age"] != age:
                message += f"\n\n⚠️ Ya tenías una suscripción activa. La he reemplazado por ésta."
    else:
        message = "¡Vaya 🥺! Parece que no te he entendido. Para que te 🔔 notifique cuando puedas pedir cita en el " \
                  "sistema de autocita de la Comunidad de Madrid, simplemente dime tu edad (ejemplo: 31) o tu año de " \
                  "nacimiento (ejemplo: 1991)"

    return message


def get_age(user_input):
    age = None

    try:
        age = int(user_input)
    except ValueError:
        regular_expressions = [r'\d+/\d+/(\d\d\d\d)', r'\d+-\d+-(\d\d\d\d)',
                               r'(\d\d\d\d)-\d+-\d+', r'(\d\d\d\d)/\d+/\d+',
                               r'(\d+)']

        i = 0
        while age is None and i < len(regular_expressions):
            groups = re.findall(regular_expressions[i], user_input)
            if groups:
                age = int(groups[len(groups) - 1])

            i += 1

    if age is not None and age >= 1900:
        age = datetime.now().year - age

    return age if age is not None and 0 <= age <= 120 else None
