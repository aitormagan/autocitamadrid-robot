import re
import os
from datetime import datetime, timedelta
from collections import defaultdict
from aws_lambda_powertools import Logger
import requests
from src import telegram_helpers
from src import db
from src.checker import get_min_years


UPDATE_CENTRES_TIME = int(os.environ.get("UPDATE_CENTRES_TIME", 300))
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
            elif message == "/mindate":
                telegram_helpers.send_text(user_id, "⌛ Esto me puede llevar unos segunditos...")
                answer = handle_min_date(update)
            else:
                answer = handle_generic_message(update)
        except Exception:
            logger.exception("Unexpected error")
            answer = "Perdoname 🙏, pero ha ocurrido un error inesperado 🤷 que me impide responder a tu solicitud. " \
                     "¿Podrías volver a intentarlo pasados unos minutos? Gracias 😃"

        update["answer"] = answer
        logger.info(update)
        telegram_helpers.send_text(user_id, answer)
    elif "my_chat_member" in update and "new_chat_member" in update["my_chat_member"] \
            and "status" in update["my_chat_member"]["new_chat_member"] \
            and update["my_chat_member"]["new_chat_member"]["status"] == "kicked":
        user_id = update["my_chat_member"]["from"]["id"]
        logger.info(f"User with id {user_id} stopped the bot")
        db.delete_notification(user_id)


def handle_start(update):
    user_info = update.get("message", {}).get("from", {})
    name = user_info.get("first_name", "")
    return f"¡Hola {name}! Bienvenido al sistema de notificación de vacunación. Si quieres que te avise 🔔 cuando " \
           f"puedas pedir cita para vacunarte 💉 en la Comunidad de Madrid, simplemente indicame la edad que " \
           f"tienes o tu año de nacimiento!\n\nOtros comandos útiles:\n-/subscribe: 🔔 Crea una suscripción para " \
           f"cuando puedas pedir cita para vacunarte\n- /help: 🙋 Muestra esta ayuda\n- /status: " \
           f"ℹ️ Muestra si ya estás suscrito\n- /cancel: 🔕 Cancela la notificación registrada\n - /currentage: " \
           f"📆 Muestra la edad mínima con la que puedes pedir cita\n - /mindate: 📆 Muestra una lista de las primeras " \
           f"citas disponibles en los distintos hospitales."


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
            message = "¡Vaya 🤔! Parece que ya te he notificado de que puedes pedir cita para vacunarte. " \
                      "Si quieres puedes crear otra suscripción: simplemente, dime la edad que tienes " \
                      "o tu año de nacimiento. ¡Estaré encantado de volver a notificarte! 📳"
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


def handle_min_date(_):

    centres_by_date, last_update = db.get_min_date_info()

    if last_update is None or (datetime.now() - last_update).seconds >= 1200:
        centres_by_date, last_update = update_centres()

    if centres_by_date:
        message = "¡Estupendo 😊! Aquí tienes las primeras fechas disponibles en el sistema de autocita:\n\n"
        for date in sorted(centres_by_date.keys()):
            date_str = date.strftime("%d/%m/%Y")
            centres = "\n".join(map(lambda x: f"- {x}", centres_by_date[date]))
            message += f"*{date_str}*:\n{centres}\n\n"

        updated_ago = int((datetime.now() - last_update).seconds / 60)
        updated_at_msg = f"Actualizado hace {updated_ago} minutos"
        updated_at_msg = updated_at_msg[:-1] if updated_ago == 1 else updated_at_msg
        message += updated_at_msg
    else:
        message = "No he sido capaz de encontrar citas disponibles. Pruébalo de nuevo más tarde."

    return message


def update_centres():
    centres_by_date = defaultdict(lambda: list())
    centres = requests.post("https://autocitavacuna.sanidadmadrid.org/ohcitacovid/autocita/obtenerCentros",
                            json={"edad_paciente": 45}, verify=False).json()

    for centre in centres:
        data_curr_month = requests.post(
            "https://autocitavacuna.sanidadmadrid.org/ohcitacovid/autocita/obtenerHuecosMes",
            json=get_spots_body(centre["idCentro"], centre["idPrestacion"], centre["agendas"]),
            verify=False).json()
        data_next_month = requests.post(
            "https://autocitavacuna.sanidadmadrid.org/ohcitacovid/autocita/obtenerHuecosMes",
            json=get_spots_body(centre["idCentro"], centre["idPrestacion"], centre["agendas"],
                                month_modified=1),
            verify=False).json()

        data = []
        data.extend(data_curr_month if type(data_curr_month) == list else [])
        data.extend(data_next_month if type(data_next_month) == list else [])
        dates = [x.get("fecha") for x in data]
        dates = [datetime.strptime(x, "%d-%m-%Y") for x in dates]
        if dates:
            centres_by_date[min(dates)].append(centre['descripcion'])

    last_update = datetime.now()
    db.save_min_date_info(centres_by_date, last_update)

    return centres_by_date, last_update


def get_spots_body(id_centre, id_prestacion, agendas, month_modified=0):
    today = datetime.now()
    check_date = datetime(year=today.year, month=today.month, day=1) + timedelta(days=31 * month_modified)

    return {
        "idPaciente": "1",
        "idPrestacion": id_prestacion,
        "agendas": agendas,
        "idCentro": id_centre,
        "mes": check_date.month,
        "anyo": check_date.year,
        "horaInicio": "08:00",
        "horaFin": "22:00"
    }
