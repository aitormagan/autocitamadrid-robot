from datetime import datetime
import telegram_helpers
import db


def handle_updates(api_response):
    update_ids = []
    if "result" in api_response:
        for update in api_response["result"]:
            update_ids.append(update.get("update_id"))
            handle_update(update)

    return max(update_ids) + 1 if update_ids else 0


def handle_update(update):
    message = update.get("message", {}).get("text", "")
    if message == "/start":
        handle_start(update)
    elif message == "/cancel":
        handle_cancel(update)
    else:
        handle_generic_message(update)


def handle_start(update):
    user_info = update.get("message", {}).get("from", {})
    name = user_info.get("first_name", "")
    message = f"¡Hola {name}! Bienvenido al sistema de notificación de vacunación. Si quieres que te avise cuando " \
              f"puedas pedir cita para vacunarte en la Comunidad de Madrid, simplemente indicame la edad que tienes " \
              f"o tu año de nacimiento!"
    telegram_helpers.send_text(user_info.get("id"), message)


def handle_cancel(update):
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    db.delete_notification(user_id)
    message = f"¡Vale {user_info.get('first_name')}! He borrado tus datos y ya no te notificaré. Si quieres volver a " \
              f"activar la suscripción, simplemente di /start"
    telegram_helpers.send_text(user_id, message)


def handle_generic_message(update):
    user_info = update.get("message", {}).get("from", {})
    received_message = update.get("message", {}).get("text", "")
    user_id = user_info.get("id")
    user_name = user_info.get('first_name')

    try:
        age = int(received_message)
        if age >= 1900:
            age = datetime.now().year - age
        db.save_notification(user_id, user_name, age)
        message = f"¡Genial {user_name}! Volverás a saber de mi cuando el sistema de autocitación " \
                  f"de la Comunidad de Madrid permita vacunarse a gente de {age} años o más jovenes. Si quieres " \
                  f"cancelar la subscipción, simplemente escribe /cancel"
    except ValueError:
        message = "¡Vaya! Parece que no te he entendido. Para que te notifique cuando puedas pedir cita en el sistema" \
                  "de autocita de la Comunidad de Madrid, simplemente dime tu edad (ejemplo: 31) o tu año de " \
                  "nacimiento (ejemplo: 1991)"

    telegram_helpers.send_text(user_id, message)


def main():
    offset = 0
    while True:
        updates = telegram_helpers.get_updates(offset)
        offset = handle_updates(updates)


if __name__ == '__main__':
    main()
