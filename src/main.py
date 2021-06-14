from datetime import datetime
import telegram_helpers
import db
from main_checker import get_min_years


def handle_updates(api_response):
    update_ids = []
    if "result" in api_response:
        for update in api_response["result"]:
            update_ids.append(update.get("update_id"))
            handle_update(update)

    return max(update_ids) + 1 if update_ids else 0


def handle_update(update):
    message = update.get("message", {}).get("text", "")
    if message in ["/start", "/help"]:
        handle_start(update)
    elif message == "/cancel":
        handle_cancel(update)
    elif message == "/status":
        handle_status(update)
    elif message == "/currentage":
        handle_current_age(update)
    else:
        handle_generic_message(update)


def handle_start(update):
    user_info = update.get("message", {}).get("from", {})
    name = user_info.get("first_name", "")
    message = f"¡Hola {name}! Bienvenido al sistema de notificación de vacunación. Si quieres que te avise 🔔 cuando " \
              f"puedas pedir cita para vacunarte 💉 en la Comunidad de Madrid, simplemente indicame la edad que " \
              f"tienes o tu año de nacimiento!\n\nOtros comandos útiles:\n- /help: 🙋 Muestra esta ayuda\n- /status: " \
              f"ℹ️ Muestra si ya estás suscrito\n- /cancel: 🔕 Cancela la notificación registrada\n - /currentage: " \
              f"📆 Muestra la edad mínima con la que puedes pedir cita"
    telegram_helpers.send_text(user_info.get("id"), message)


def handle_cancel(update):
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    db.delete_notification(user_id)
    message = f"¡Vale {user_info.get('first_name')}! He borrado ❌ tus datos y ya no te notificaré. Si quieres volver " \
              f"a activar la suscripción, simplemente di /start"
    telegram_helpers.send_text(user_id, message)


def handle_status(update):
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    user_notification = db.get_user_notification(user_id)
    if user_notification:
        age = user_notification["age"]
        if user_notification["notified"]:
            message = "¡Genial! Ya tienes activas las notificaciones 🔔 para cuando el sistema de autocita permita " \
                      f"pedir cita a personas de {age} o más años. Si quieres cancelarla, simplemente escribe /cancel."
        else:
            message = f"¡Vaya! Parece que ya te he notificado de que las personas de {age} o más años pueden " \
                      f"pedir cita. Si quieres puedes crear otra suscripción  dime la edad que tienes " \
                      f"o tu año de nacimiento. ¡Estaré encantado de volver a notificarte! 😉"
    else:
        message = "Actualmente no tienes ninguna notificación registrada 😓. Si quieres que te notifique 🔔 cuando " \
                  "puedas pedir cita para vacunarte simplemente dime tu año de nacimiento o tu edad."
    telegram_helpers.send_text(user_id, message)


def handle_current_age(update):
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    min_years = get_min_years()
    message = f"El sistema de autocita permite pedir cita a personas con {min_years} años o más️. Si cumples con " \
              f"la edad, puedes ir a 🔗 https://autocitavacuna.sanidadmadrid.org/ohcitacovid para pedir tu cita"
    telegram_helpers.send_text(user_id, message)


def handle_generic_message(update):
    user_info = update.get("message", {}).get("from", {})
    received_message = update.get("message", {}).get("text", "")
    user_id = user_info.get("id")
    user_name = user_info.get('first_name')

    try:
        age = int(received_message)
        min_years = get_min_years()
        if age >= 1900:
            age = datetime.now().year - age

        if age >= min_years:
            message = "‼️ ¡Ey! Parece que el sistema ya te permite pedir cita. ¡Hazlo ya en 🔗 " \
                      "https://autocitavacuna.sanidadmadrid.org/ohcitacovid/!"
        else:
            db.save_notification(user_id, user_name, age)
            message = f"¡Genial {user_name} 😊! Volverás a saber de mi cuando el sistema de autocitación " \
                      f"de la Comunidad de Madrid permita pedir cita a gente con {age} años. Si quieres " \
                      f"❌ cancelar la suscripción, simplemente escribe /cancel.\n\nPD: Si tuvieras una notificación " \
                      f"establecida anteriormente, ha sido sustituida por esta última."
    except ValueError:
        message = "¡Vaya 🥺! Parece que no te he entendido. Para que te 🔔 notifique cuando puedas pedir cita en el " \
                  "sistema de autocita de la Comunidad de Madrid, simplemente dime tu edad (ejemplo: 31) o tu año de " \
                  "nacimiento (ejemplo: 1991)"

    telegram_helpers.send_text(user_id, message)


def main():
    offset = 0
    while True:
        updates = telegram_helpers.get_updates(offset)
        print(updates)
        offset = handle_updates(updates)


if __name__ == '__main__':
    main()
