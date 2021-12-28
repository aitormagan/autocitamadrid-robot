from unittest.mock import patch
from freezegun import freeze_time
from src import message_handler


@freeze_time("2021-12-29 06:59:59", tz_offset=-1)
@patch("src.message_handler.db")
@patch("src.message_handler.requests")
def test_given_just_before_new_date_of_birth_allowed_when_handle_current_age_then_all_info_returned(requests_mock,
                                                                                                    db_mock):
    requests_mock.get.return_value.json.return_value = {
        "dFin_Birthday": "31/12/2016"
    }
    db_mock.get_info_third_dose.return_value = {
        "new_date_of_birth": 1956,
        "previous_date_of_birth": 1966,
        "new_date_of_birth_date": "29/12/2021"
    }

    messages = message_handler.handle_current_age()

    assert len(messages) == 4

    assert "primeras citas, el sistema permite pedir cita a personas nacidas en 2016 o antes." in messages[0]
    assert "el sistema de autocita permite pedir cita a personas nacidas en 1966 o antes" in messages[1]
    assert "Desde el 📅 29/12/2021 a las 07:00, las personas nacidas en 1956 o antes podrán pedir cita" in messages[2]


@freeze_time("2021-12-29 07:00:01", tz_offset=-1)
@patch("src.message_handler.db")
@patch("src.message_handler.requests")
# dob = Date Of Birth
def test_given_just_after_new_date_of_birth_allowed_when_handle_current_age_then_updated_dob_returned(requests_mock,
                                                                                                      db_mock):
    requests_mock.get.return_value.json.return_value = {
        "dFin_Birthday": "31/12/2016"
    }
    db_mock.get_info_third_dose.return_value = {
        "new_date_of_birth": 1956,
        "previous_date_of_birth": 1966,
        "new_date_of_birth_date": "29/12/2021"
    }

    messages = message_handler.handle_current_age()

    assert len(messages) == 3

    assert "primeras citas, el sistema permite pedir cita a personas nacidas en 2016 o antes." in messages[0]
    assert "el sistema de autocita permite pedir cita a personas nacidas en 1956 o antes" in messages[1]
