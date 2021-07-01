from unittest.mock import patch, MagicMock, ANY, call
from freezegun import freeze_time
from func_timeout.exceptions import FunctionTimedOut
from src import checker


@freeze_time("2021-06-23")
@patch("src.checker.send_text")
def test_when_notify_then_notification_sent(send_text_mock):
    min_age = 31
    user_id = MagicMock()
    name = "Aitor"

    checker.notify(min_age, {"user_id": user_id, "name": name})

    send_text_mock.assert_called_once_with(user_id, ANY)
    notification = send_text_mock.call_args[0][1]
    assert f"Buenas noticias {name}" in notification
    assert f"permite pedir cita a gente nacida en 1990 o antes" in notification


@patch("src.checker.save_notification")
def test_when_mark_as_notified_then_db_updated(save_notification_mock):
    user_id = MagicMock()
    name = "Aitor"
    age = 30

    checker.mark_as_notified({"user_id": user_id, "name": name, "age": age})

    save_notification_mock.assert_called_once_with(user_id, name, age, True)


@patch("src.checker.requests")
@patch("src.checker.save_min_years")
@freeze_time("2021-06-20")
def test_given_1990_as_year_when_get_min_years_then_31_returned(save_min_years_mock, requests_mock):
    requests_mock.get.return_value.json.return_value = {
        "dFin_Birthday": "31/12/1990"
    }

    assert checker.get_min_years() == 31
    save_min_years_mock.assert_called_once_with(31)


@patch("src.checker.mark_as_notified")
@patch("src.checker.notify")
@patch("src.checker.get_non_notified_people")
@patch("src.checker.get_min_years", return_value=45)
def test_when_main_then_only_people_above_min_age_notified(get_min_years_mock, get_non_notified_people_mock,
                                                           notify_mock, mark_as_notified_mock):

    get_non_notified_people_mock.return_value = [
        {
            "user_id": MagicMock(),
            "name": MagicMock(),
            "age": 44,
            "notified": False
        }, {
            "user_id": MagicMock(),
            "name": MagicMock(),
            "age": 45,
            "notified": False
        }, {
            "user_id": MagicMock(),
            "name": MagicMock(),
            "age": 46,
            "notified": False
        }
    ]

    checker.main()

    notify_mock.assert_has_calls([call(45, get_non_notified_people_mock.return_value[1]),
                                  call(45, get_non_notified_people_mock.return_value[2])])
    mark_as_notified_mock.assert_has_calls([call(get_non_notified_people_mock.return_value[1]),
                                            call(get_non_notified_people_mock.return_value[2])])
