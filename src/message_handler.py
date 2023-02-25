from aws_lambda_powertools import Logger
from src import telegram_helpers


logger = Logger(service="vacunacovidmadridbot")


def handle_update(update):
    user_info = update.get("message", {}).get("from", {})
    user_id = user_info.get("id")
    name = user_info.get("first_name", "")

    if user_id:
        answers = [f"Hola {name}. Por suerte este bot ya ha dejado de tener sentido: "
                   "la COVID sigue en nuestras vidas, pero ahora convivimos con ella "
                   "de la misma forma que con otras enfermedades. Espero haberte sido "
                   "de ayuda durante el tiempo en que estuve operativo.",

                   "🤔 ¿Vives en Madrid? ¿Usas mucho el metro? ¡Ahora tienes un nuevo "
                   "🤖 bot disponible! Con "
                   "[Metro Madrid - Tiempos de Espera](t.me/MetroMadridTiempoEsperaBot) "
                   "puedes obtener los tiempos de espera en cualquier 🚇 estación de metro "
                   "con simplemente 🗣️ decir el nombre o mandar tu 📍 ubicación.\n\n¡No "
                   "esperes más y pruébalo ya!",

                   "👋 ¡Hasta otra! 👋"]

        for answer in answers:
            telegram_helpers.send_text(user_id, answer)
    elif "my_chat_member" in update and "new_chat_member" in update["my_chat_member"] \
            and "status" in update["my_chat_member"]["new_chat_member"] \
            and update["my_chat_member"]["new_chat_member"]["status"] == "kicked":
        user_id = update["my_chat_member"]["from"]["id"]
        logger.info(f"User with id {user_id} stopped the bot")
