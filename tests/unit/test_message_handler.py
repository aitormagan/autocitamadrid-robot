from unittest.mock import patch, MagicMock, ANY, call
from datetime import datetime
import pytest
from freezegun import freeze_time
from src import message_handler


@pytest.mark.parametrize("text,expected_age", [
    ("1990", 31),
    ("30", 30),
    ("0", 0),
    ("2/2/1990", 31),
    ("2 de febrero de 1990", 31),
    ("/subscribe 31", 31),
    ("/subscribe 1990", 31),
    ("1720", None),
    ("gracias", None)
])
@freeze_time("2021-06-20")
def test_get_age(text, expected_age):
    assert message_handler.get_age(text) == expected_age


@patch("src.message_handler.db.get_min_years", return_value=45)
@patch("src.message_handler.get_age", return_value=45)
def test_given_age_above_min_years_when_handle_generic_then_you_can_already_join(get_age_mock, get_min_years_mock):
    text = MagicMock()
    user_id = MagicMock()
    first_name = "Aitor"

    result = message_handler.handle_generic_message({
        "message": {
            "text": text,
            "from": {
                "id": user_id,
                "first_name": first_name
            }
        }
    })

    assert "te permite pedir cita" in result

    get_age_mock.assert_called_once_with(text)
    get_min_years_mock.assert_called_once_with()


@patch("src.message_handler.db.get_min_years", return_value=45)
@patch("src.message_handler.get_age", return_value=None)
def test_given_no_age_when_handle_generic_then_not_understood(get_age_mock, get_min_years_mock):
    text = MagicMock()
    user_id = MagicMock()
    first_name = "Aitor"

    result = message_handler.handle_generic_message({
        "message": {
            "text": text,
            "from": {
                "id": user_id,
                "first_name": first_name
            }
        }
    })

    assert "no te he entendido" in result

    get_age_mock.assert_called_once_with(text)
    get_min_years_mock.assert_not_called()


@freeze_time("2021-06-23")
@patch("src.message_handler.db.get_min_years", return_value=45)
@patch("src.message_handler.get_age", return_value=44)
@patch("src.message_handler.db")
def test_given_below_when_handle_generic_then_subscription(db_mock, get_age_mock, get_min_years_mock):
    text = MagicMock()
    user_id = MagicMock()
    first_name = "Aitor"
    db_mock.get_user_notification.return_value = None

    result = message_handler.handle_generic_message({
        "message": {
            "text": text,
            "from": {
                "id": user_id,
                "first_name": first_name
            }
        }
    })

    assert "permita pedir cita a gente nacida en 1977" in result
    assert "Ya tenías" not in result

    get_age_mock.assert_called_once_with(text)
    get_min_years_mock.assert_called_once_with()
    db_mock.save_notification.assert_called_once_with(user_id, first_name, 44)


@freeze_time("2021-06-23")
@patch("src.message_handler.db.get_min_years", return_value=45)
@patch("src.message_handler.get_age", return_value=44)
@patch("src.message_handler.db")
def test_given_below_and_previous_subscription_when_handle_generic_then_alert_message(db_mock, get_age_mock,
                                                                                      get_min_years_mock):
    text = MagicMock()
    user_id = MagicMock()
    first_name = "Aitor"
    db_mock.get_user_notification.return_value = {"age": 30}

    result = message_handler.handle_generic_message({
        "message": {
            "text": text,
            "from": {
                "id": user_id,
                "first_name": first_name
            }
        }
    })

    assert "permita pedir cita a gente nacida en 1977" in result
    assert "Ya tenías" in result

    get_age_mock.assert_called_once_with(text)
    get_min_years_mock.assert_called_once_with()
    db_mock.save_notification.assert_called_once_with(user_id, first_name, 44)


@patch("src.message_handler.db")
def test_when_handle_cancel_then_element_deleted(db_mock):

    user_id = MagicMock()
    first_name = MagicMock()

    result = message_handler.handle_cancel({
        "message": {
            "text": MagicMock(),
            "from": {
                "id": user_id,
                "first_name": first_name
            }
        }
    })

    assert "He borrado" in result

    db_mock.delete_notification.assert_called_once_with(user_id)


@patch("src.message_handler.db")
def test_given_not_subscribed_when_handle_status_then_no_subscription(db_mock):
    db_mock.get_user_notification.return_value = None
    user_id = MagicMock()

    result = message_handler.handle_status({
        "message": {
            "text": MagicMock(),
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    assert "no tienes ninguna notificación registrada" in result
    db_mock.get_user_notification.assert_called_once_with(user_id)


@patch("src.message_handler.db")
def test_given_subscribed_not_notified_when_handle_status_then_everything_ok(db_mock):
    db_mock.get_user_notification.return_value = {"age": 30, "notified": False}
    user_id = MagicMock()

    result = message_handler.handle_status({
        "message": {
            "text": MagicMock(),
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    assert "Todo listo" in result
    db_mock.get_user_notification.assert_called_once_with(user_id)


@patch("src.message_handler.db")
def test_given_subscribed_notified_when_handle_status_then_already_notified(db_mock):
    db_mock.get_user_notification.return_value = {"age": 30, "notified": True}
    user_id = MagicMock()

    result = message_handler.handle_status({
        "message": {
            "text": MagicMock(),
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    assert "Parece que ya te he notificado" in result
    db_mock.get_user_notification.assert_called_once_with(user_id)


@freeze_time("2021-06-23")
@patch("src.message_handler.db")
def test_given_not_subscribed_when_handle_current_age_then_you_can_subscribe(db_mock):
    db_mock.get_user_notification.return_value = None
    db_mock.get_min_years.return_value = 45
    user_id = MagicMock()

    result = message_handler.handle_current_age({
        "message": {
            "text": MagicMock(),
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    assert "pedir cita a personas a personas nacidas en 1976 o antes"
    assert "Puedo notificarte" in result
    db_mock.get_user_notification.assert_called_once_with(user_id)


@freeze_time("2021-06-23")
@patch("src.message_handler.db")
def test_given_subscribed_when_handle_current_age_then_message_with_age(db_mock):
    db_mock.get_user_notification.return_value = MagicMock()
    db_mock.get_min_years.return_value = 45
    user_id = MagicMock()

    result = message_handler.handle_current_age({
        "message": {
            "text": MagicMock(),
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    assert "pedir cita a personas a personas nacidas en 1976 o antes"
    assert "Puedo notificarte" not in result
    db_mock.get_user_notification.assert_called_once_with(user_id)


def test_when_handle_subscribe_then_ask_for_age():
    name = "Aitor"

    answer = message_handler.handle_subscribe({
        "message": {
            "from": {
                "first_name": name
            }
        }
    })

    assert name in answer
    assert "tu año de nacimiento" in answer


def test_when_handle_start_then_ask_for_age():
    name = "Aitor"

    answer = message_handler.handle_start({
        "message": {
            "from": {
                "first_name": name
            }
        }
    })

    assert name in answer
    assert "año de nacimiento" in answer
    assert "Otros comandos útiles" in answer
    assert "/help" in answer
    assert "/subscribe" in answer
    assert "/cancel" in answer
    assert "/status" in answer
    assert "/currentage" in answer


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_start_when_handle_update_then_handle_start_called(handle_generic_message_mock, handle_subscribe_mock,
                                                                 handle_current_age_mock, handle_status_mock,
                                                                 handle_cancel_mock, handle_start_mock,
                                                                 telegram_helpers_mock, handle_min_date_mock):
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "/start",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_called_once_with(user_id, handle_start_mock.return_value)


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_help_when_handle_update_then_handle_start_called(handle_generic_message_mock, handle_subscribe_mock,
                                                                handle_current_age_mock, handle_status_mock,
                                                                handle_cancel_mock, handle_start_mock,
                                                                telegram_helpers_mock, handle_min_date_mock):
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "/help",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_called_once_with(user_id, handle_start_mock.return_value)


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_cancel_when_handle_update_then_handle_cancel_called(handle_generic_message_mock, handle_subscribe_mock,
                                                                   handle_current_age_mock, handle_status_mock,
                                                                   handle_cancel_mock, handle_start_mock,
                                                                   telegram_helpers_mock, handle_min_date_mock):
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "/cancel",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_called_once_with(user_id, handle_cancel_mock.return_value)


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_status_when_handle_update_then_handle_status_called(handle_generic_message_mock, handle_subscribe_mock,
                                                                   handle_current_age_mock, handle_status_mock,
                                                                   handle_cancel_mock, handle_start_mock,
                                                                   telegram_helpers_mock, handle_min_date_mock):
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "/status",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_called_once_with(user_id, handle_status_mock.return_value)


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_currentage_when_handle_update_then_handle_current_age_called(handle_generic_message_mock, handle_subscribe_mock,
                                                                            handle_current_age_mock, handle_status_mock,
                                                                            handle_cancel_mock, handle_start_mock,
                                                                            telegram_helpers_mock,
                                                                            handle_min_date_mock):
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "/currentage",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_called_once_with(user_id, handle_current_age_mock.return_value)


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_subscribe_when_handle_update_then_handle_subscribe_called(handle_generic_message_mock, handle_subscribe_mock,
                                                                         handle_current_age_mock, handle_status_mock,
                                                                         handle_cancel_mock, handle_start_mock,
                                                                         telegram_helpers_mock, handle_min_date_mock):
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "/subscribe",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_called_once_with(user_id, handle_subscribe_mock.return_value)


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_min_date_when_handle_update_then_handle_min_date_called(handle_generic_message_mock, handle_subscribe_mock,
                                                                         handle_current_age_mock, handle_status_mock,
                                                                         handle_cancel_mock, handle_start_mock,
                                                                         telegram_helpers_mock, handle_min_date_mock):
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "/mindate",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_any_call(user_id, ANY)


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_random_text_when_handle_update_then_handle_generic_text_called(handle_generic_message_mock,
                                                                              handle_subscribe_mock,
                                                                              handle_current_age_mock,
                                                                              handle_status_mock,
                                                                              handle_cancel_mock,
                                                                              handle_start_mock,
                                                                              telegram_helpers_mock,
                                                                              handle_min_date_mock):
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "1990",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_called_once_with(user_id, handle_generic_message_mock.return_value)


@patch("src.message_handler.handle_min_date")
@patch("src.message_handler.telegram_helpers")
@patch("src.message_handler.handle_start")
@patch("src.message_handler.handle_cancel")
@patch("src.message_handler.handle_status")
@patch("src.message_handler.handle_current_age")
@patch("src.message_handler.handle_subscribe")
@patch("src.message_handler.handle_generic_message")
def test_given_exception_when_handle_update_then_sorry_message(handle_generic_message_mock,
                                                               handle_subscribe_mock,
                                                               handle_current_age_mock,
                                                               handle_status_mock,
                                                               handle_cancel_mock,
                                                               handle_start_mock,
                                                               telegram_helpers_mock,
                                                               handle_min_date_mock):

    handle_generic_message_mock.side_effect = Exception()
    user_id = MagicMock()
    message_handler.handle_update({
        "message": {
            "text": "1990",
            "from": {
                "id": user_id,
                "first_name": MagicMock()
            }
        }
    })

    telegram_helpers_mock.send_text.assert_called_once_with(user_id, ANY)
    assert "Perdoname" in telegram_helpers_mock.send_text.call_args[0][1]


@patch("src.message_handler.db")
def test_given_user_kicked_bot_when_handle_update_then_notification_cancelled(db_mock):
    user_id = MagicMock()
    message = {
        "my_chat_member": {
            "chat": {
                "id": user_id,
                "first_name": "Aitor",
                "type": "private"
            },
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Aitor",
                "language_code": "es"
            },
            "old_chat_member": {
                "user": {
                    "id": MagicMock(),
                    "is_bot": True,
                    "first_name": "Vacuna Covid Madrid",
                    "username": "vacunacovidmadridbot"
                },
                "status": "member"
            },
            "new_chat_member": {
                "user": {
                    "id": MagicMock(),
                    "is_bot": True,
                    "first_name": "Vacuna Covid Madrid",
                    "username": "vacunacovidmadridbot"
                },
                "status": "kicked",
                "until_date": 0
            }
        }
    }

    message_handler.handle_update(message)

    db_mock.delete_notification.assert_called_once_with(user_id)


@freeze_time("2021-06-22 18:20:00")
@patch("src.message_handler.update_centres")
@patch("src.message_handler.db")
@patch("src.message_handler.UPDATE_CENTRES_TIME", 1200)
def test_given_info_not_updated_when_handle_min_date_then_update_centres_called(db_mock, update_centres_mock):
    centres = {
        datetime(2021, 3, 6): ["hosp1", "hosp2"],
        datetime(2021, 5, 9): ["hosp3", "hosp4"]
    }
    db_mock.get_min_date_info.return_value = ({}, datetime(2021, 6, 22, 17, 59, 00))
    update_centres_mock.return_value = (centres, datetime(2021, 6, 22, 18, 20, 00))

    answer = message_handler.handle_min_date(None)

    update_centres_mock.assert_called_once_with()
    db_mock.get_min_date_info.assert_called_once_with()

    assert "*06/03/2021*:\n- hosp1\n- hosp2" in answer
    assert "*09/05/2021*:\n- hosp3\n- hosp4" in answer
    assert "Actualizado hace 0 minutos" in answer


@freeze_time("2021-06-22 18:20:00")
@patch("src.message_handler.update_centres")
@patch("src.message_handler.db")
@patch("src.message_handler.UPDATE_CENTRES_TIME", 1200)
def test_given_info_updated_when_handle_min_date_then_update_centres_not_called(db_mock, update_centres_mock):
    centres = {
        datetime(2021, 3, 6): ["hosp1", "hosp2"],
        datetime(2021, 5, 9): ["hosp3", "hosp4"]
    }
    db_mock.get_min_date_info.return_value = (centres, datetime(2021, 6, 22, 18, 00, 1))

    answer = message_handler.handle_min_date(None)

    update_centres_mock.assert_not_called()

    assert "*06/03/2021*:\n- hosp1\n- hosp2" in answer
    assert "*09/05/2021*:\n- hosp3\n- hosp4" in answer
    assert "Actualizado hace 20 minutos" in answer


@freeze_time("2021-06-22 10:01:02")
@patch("src.message_handler.requests")
@patch("src.message_handler.get_centre_min_date")
@patch("src.message_handler.db")
def test_given_one_centres_no_date_when_update_centres_then_info_empty(db_mock, get_centre_min_date,
                                                                           requests_mock):

    hosp = MagicMock()
    centres_response = [
        hosp
    ]

    get_centre_min_date.return_value = None

    requests_mock.post.return_value.json.return_value = centres_response

    centres, last_update = message_handler.update_centres()

    assert dict(centres) == {
    }

    get_centre_min_date.assert_called_once_with(hosp)
    db_mock.save_min_date_info.assert_called_once_with(centres, last_update)


@freeze_time("2021-06-22 10:01:02")
@patch("src.message_handler.requests")
@patch("src.message_handler.get_centre_min_date")
@patch("src.message_handler.db")
def test_given_two_centres_same_date_when_update_centres_then_info_grouped(db_mock, get_centre_min_date,
                                                                           requests_mock):

    hosp1 = {
        "descripcion": "hosp1"
    }
    hosp2 = {
        "descripcion": "hosp2"
    }

    centres_response = [
        hosp1, hosp2
    ]

    get_centre_min_date.return_value = datetime(2021, 6, 28)

    requests_mock.post.return_value.json.return_value = centres_response

    centres, last_update = message_handler.update_centres()

    assert dict(centres) == {
        datetime(2021, 6, 28): ["hosp1", "hosp2"]
    }

    get_centre_min_date.assert_has_calls([call(hosp1), call(hosp2)])
    db_mock.save_min_date_info.assert_called_once_with(centres, last_update)


@freeze_time("2021-06-22 10:01:02")
@patch("src.message_handler.requests")
@patch("src.message_handler.get_centre_min_date")
@patch("src.message_handler.db")
def test_given_two_centres_diff_date_when_update_centres_then_info_separated(db_mock, get_centre_min_date,
                                                                             requests_mock):

    hosp1 = {
        "descripcion": "hosp1"
    }
    hosp2 = {
        "descripcion": "hosp2"
    }

    centres_response = [
        hosp1, hosp2
    ]

    get_centre_min_date.side_effect = [datetime(2021, 6, 28), datetime(2021, 6, 30)]

    requests_mock.post.return_value.json.return_value = centres_response

    centres, last_update = message_handler.update_centres()

    assert dict(centres) == {
        datetime(2021, 6, 28): ["hosp1"],
        datetime(2021, 6, 30): ["hosp2"]
    }

    get_centre_min_date.assert_has_calls([call(hosp1), call(hosp2)])
    db_mock.save_min_date_info.assert_called_once_with(centres, last_update)

@freeze_time("2021-06-22 10:01:02")
@patch("src.message_handler.requests")
@patch("src.message_handler.get_spots_body")
def test_given_data_in_current_month_when_get_centre_mindate_then_only_one_schedule_request_made(get_spots_body_mock,
                                                                                                 requests_mock):
    hosp_id = 1
    hosp_desc = "hosp1"
    hosp_agendas = MagicMock()
    hosp_prestacion = "123"

    centre = {
        "idCentro": hosp_id,
        "descripcion": hosp_desc,
        "agendas": hosp_agendas,
        "idPrestacion": hosp_prestacion
    }

    hosp_spots = [
        {
            "fecha": "29-06-2021"
        },
        {
            "fecha": "28-06-2021"
        }
    ]

    requests_mock.post.return_value.json.return_value = hosp_spots

    min_date = message_handler.get_centre_min_date(centre)

    assert min_date == datetime(2021, 6, 28)
    requests_mock.post.assert_called_once_with(ANY, json=get_spots_body_mock.return_value, verify=False)
    get_spots_body_mock.assert_called_once_with(hosp_id, hosp_prestacion, hosp_agendas)


@freeze_time("2021-06-22 10:01:02")
@patch("src.message_handler.requests")
@patch("src.message_handler.get_spots_body")
def test_given_no_data_in_current_month_when_get_centre_mindate_then_two_schedule_request_made(get_spots_body_mock,
                                                                                               requests_mock):
    hosp_id = 1
    hosp_desc = "hosp1"
    hosp_agendas = MagicMock()
    hosp_prestacion = "123"

    body1 = MagicMock()
    body2 = MagicMock()
    get_spots_body_mock.side_effect = [body1, body2]

    centre = {
        "idCentro": hosp_id,
        "descripcion": hosp_desc,
        "agendas": hosp_agendas,
        "idPrestacion": hosp_prestacion
    }

    hosp_spots = [
        {
            "fecha": "29-07-2021"
        },
        {
            "fecha": "28-07-2021"
        }
    ]

    requests_mock.post.return_value.json.side_effect = [[], hosp_spots]

    min_date = message_handler.get_centre_min_date(centre)

    assert min_date == datetime(2021, 7, 28)

    requests_mock.post.assert_has_calls([call(ANY, json=body1, verify=False),
                                         call().json(),
                                         call(ANY, json=body2, verify=False),
                                         call().json()])
    get_spots_body_mock.assert_has_calls([call(hosp_id, hosp_prestacion, hosp_agendas),
                                          call(hosp_id, hosp_prestacion, hosp_agendas, month_modifier=1)])


@freeze_time("2021-06-22 10:01:02")
@patch("src.message_handler.requests")
@patch("src.message_handler.get_spots_body")
def test_given_curr_month_not_a__list_when_get_centre_mindate_then_two_schedule_request_made(get_spots_body_mock,
                                                                                             requests_mock):
    hosp_id = 1
    hosp_desc = "hosp1"
    hosp_agendas = MagicMock()
    hosp_prestacion = "123"

    body1 = MagicMock()
    body2 = MagicMock()
    get_spots_body_mock.side_effect = [body1, body2]

    centre = {
        "idCentro": hosp_id,
        "descripcion": hosp_desc,
        "agendas": hosp_agendas,
        "idPrestacion": hosp_prestacion
    }

    hosp_spots = [
        {
            "fecha": "29-07-2021"
        },
        {
            "fecha": "28-07-2021"
        }
    ]

    requests_mock.post.return_value.json.side_effect = [{}, hosp_spots]

    min_date = message_handler.get_centre_min_date(centre)

    assert min_date == datetime(2021, 7, 28)

    requests_mock.post.assert_has_calls([call(ANY, json=body1, verify=False),
                                         call().json(),
                                         call(ANY, json=body2, verify=False),
                                         call().json()])
    get_spots_body_mock.assert_has_calls([call(hosp_id, hosp_prestacion, hosp_agendas),
                                          call(hosp_id, hosp_prestacion, hosp_agendas, month_modifier=1)])


@freeze_time("2021-06-22 10:01:02")
@patch("src.message_handler.requests")
@patch("src.message_handler.get_spots_body")
def test_given_no_data_in_both_months_when_get_centre_mindate_then_none_returned(get_spots_body_mock,
                                                                                 requests_mock):
    hosp_id = 1
    hosp_desc = "hosp1"
    hosp_agendas = MagicMock()
    hosp_prestacion = "123"

    body1 = MagicMock()
    body2 = MagicMock()
    get_spots_body_mock.side_effect = [body1, body2]

    centre = {
        "idCentro": hosp_id,
        "descripcion": hosp_desc,
        "agendas": hosp_agendas,
        "idPrestacion": hosp_prestacion
    }

    requests_mock.post.return_value.json.side_effect = [[], []]

    min_date = message_handler.get_centre_min_date(centre)

    assert min_date is None

    requests_mock.post.assert_has_calls([call(ANY, json=body1, verify=False),
                                         call().json(),
                                         call(ANY, json=body2, verify=False),
                                         call().json()])
    get_spots_body_mock.assert_has_calls([call(hosp_id, hosp_prestacion, hosp_agendas),
                                          call(hosp_id, hosp_prestacion, hosp_agendas, month_modifier=1)])


@freeze_time("2021-06-22 10:01:02")
@patch("src.message_handler.requests")
@patch("src.message_handler.get_spots_body")
def test_given_info_not_a_list_in_both_months_when_get_centre_mindate_then_none_returned(get_spots_body_mock,
                                                                                         requests_mock):
    hosp_id = 1
    hosp_desc = "hosp1"
    hosp_agendas = MagicMock()
    hosp_prestacion = "123"

    body1 = MagicMock()
    body2 = MagicMock()
    get_spots_body_mock.side_effect = [body1, body2]

    centre = {
        "idCentro": hosp_id,
        "descripcion": hosp_desc,
        "agendas": hosp_agendas,
        "idPrestacion": hosp_prestacion
    }

    requests_mock.post.return_value.json.side_effect = [{}, {}]

    min_date = message_handler.get_centre_min_date(centre)

    assert min_date is None

    requests_mock.post.assert_has_calls([call(ANY, json=body1, verify=False),
                                         call().json(),
                                         call(ANY, json=body2, verify=False),
                                         call().json()])
    get_spots_body_mock.assert_has_calls([call(hosp_id, hosp_prestacion, hosp_agendas),
                                          call(hosp_id, hosp_prestacion, hosp_agendas, month_modifier=1)])


@freeze_time("2021-06-22")
def test_given_1_month_modifier_when_get_spots_body_then_next_month_returned_in_mes():
    id_centre = "123"
    id_prestacion = "456"
    agendas = MagicMock()
    month_modifier = 1

    assert message_handler.get_spots_body(id_centre, id_prestacion, agendas, month_modifier) == {
        "idPaciente": "1",
        "idPrestacion": id_prestacion,
        "agendas": agendas,
        "idCentro": id_centre,
        "mes": 7,
        "anyo": 2021,
        "horaInicio": "00:00",
        "horaFin": "23:59"
    }


@freeze_time("2021-06-22")
def test_given_0_month_modifier_when_get_spots_body_then_current_month_returned_in_mes():
    id_centre = "123"
    id_prestacion = "456"
    agendas = MagicMock()
    month_modifier = 0

    assert message_handler.get_spots_body(id_centre, id_prestacion, agendas, month_modifier) == {
        "idPaciente": "1",
        "idPrestacion": id_prestacion,
        "agendas": agendas,
        "idCentro": id_centre,
        "mes": 6,
        "anyo": 2021,
        "horaInicio": "00:00",
        "horaFin": "23:59"
    }
