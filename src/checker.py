import requests
from aws_lambda_powertools import Logger
from datetime import datetime
from src.telegram_helpers import send_text
from src.db import save_notification, get_non_notified_people

logger = Logger(service="vacunacovidmadridbot")


def notify(user_info):
    message = f"‼️ ¡Buenas noticias {user_info['name']}! El sistema de vacunación de la Comunidad de Madrid ya " \
              f"permite pedir cita a gente con {user_info['age']} años o más. ¡🏃 Corre y pide tu cita en 🔗 " \
              f"https://autocitavacuna.sanidadmadrid.org/ohcitacovid/!"
    send_text(user_info["user_id"], message)


def mark_as_notified(user_info):
    save_notification(user_info["user_id"], user_info["name"], user_info["age"], True)


def get_min_years():
    data = requests.get("https://autocitavacuna.sanidadmadrid.org/ohcitacovid/assets/config/app-config.json",
                        verify=False).json()

    max_birthday = datetime.strptime(data["dFin_Birthday"], "%d/%m/%Y")
    curr_date = datetime.now()
    return curr_date.year - max_birthday.year


def main():
    min_years = get_min_years()
    non_notified = get_non_notified_people()

    for person in non_notified:
        if min_years <= person.get("age"):
            logger.info(f"Notifying user with id {person['user_id']}")
            notify(person)
            mark_as_notified(person)
