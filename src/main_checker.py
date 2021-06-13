import requests
from datetime import datetime
from telegram_helpers import send_text
from db import save_notification, get_non_notified_people


def notify(user_info):
    message = f"¡Buenas noticias {user_info['name']}! El sistema de vacunación de la Comunidad de Madrid ya permite " \
              f"pedir cita a gente con {user_info['age']} o menos. !Corre y pide tu cita en " \
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
            notify(person)
            mark_as_notified(person)


if __name__ == '__main__':
    main()
