from unittest.mock import patch, MagicMock, ANY
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


@patch("src.message_handler.get_min_years", return_value=45)
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


@patch("src.message_handler.get_min_years", return_value=45)
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


@patch("src.message_handler.get_min_years", return_value=45)
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

    assert "permita pedir cita a gente con 44 años" in result
    assert "Ya tenías" not in result

    get_age_mock.assert_called_once_with(text)
    get_min_years_mock.assert_called_once_with()
    db_mock.save_notification.assert_called_once_with(user_id, first_name, 44)


@patch("src.message_handler.get_min_years", return_value=45)
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

    assert "permita pedir cita a gente con 44 años" in result
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


@patch("src.message_handler.db")
@patch("src.message_handler.get_min_years", return_value=45)
def test_given_not_subscribed_when_handle_current_age_then_you_can_subscribe(get_min_years_mock, db_mock):
    db_mock.get_user_notification.return_value = None
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

    assert "pedir cita a personas con 45 años o más️" in result
    assert "Puedo notificarte" in result
    db_mock.get_user_notification.assert_called_once_with(user_id)


@patch("src.message_handler.db")
@patch("src.message_handler.get_min_years", return_value=45)
def test_given_subscribed_when_handle_current_age_then_message_with_age(get_min_years_mock, db_mock):
    db_mock.get_user_notification.return_value = MagicMock()
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

    assert "pedir cita a personas con 45 años o más️" in result
    assert "Puedo notificarte" not in result
    db_mock.get_user_notification.assert_called_once_with(user_id)


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
                                                                 telegram_helpers_mock):
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
                                                                telegram_helpers_mock):
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
                                                                   telegram_helpers_mock):
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
                                                                   telegram_helpers_mock):
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
                                                                            telegram_helpers_mock):
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
                                                                         telegram_helpers_mock):
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
                                                                              telegram_helpers_mock):
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
                                                               telegram_helpers_mock):

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








