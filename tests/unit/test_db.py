from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import pytest
from src import db
from src.exceptions import ImpossibleToDetermineMaxAge


TABLE_NAME = "test-table"


class ParameterNotFound(BaseException):
    pass


@patch("src.db.CLIENT")
@patch("src.db.TABLE_NAME", TABLE_NAME)
def test_given_user_info_when_save_notification_then_put_item_called(client_mock):

    user_id = MagicMock()
    name = MagicMock()
    age = MagicMock()
    notified = True

    db.save_notification(user_id, name, age, notified)

    client_mock.put_item(TableName=TABLE_NAME, Item={"user_id": {"S": str(user_id)}, "name": {"S": name},
                                                     "age": {"N": str(age)}, "notified": {"BOOL": notified}})


@patch("src.db.CLIENT")
@patch("src.db.TABLE_NAME", TABLE_NAME)
def test_given_user_id_when_delete_notification_then_delete_item_called(client_mock):

    user_id = MagicMock()

    db.delete_notification(user_id)

    client_mock.delete_item(TableName=TABLE_NAME, Key={"user_id": {"S": str(user_id)}})


@patch("src.db.CLIENT")
@patch("src.db.TABLE_NAME", TABLE_NAME)
def test_given_no_notification_when_get_user_notification_then_none_returned(client_mock):

    user_id = MagicMock()
    client_mock.get_item.return_value = {"Item": None}

    assert db.get_user_notification(user_id) is None

    client_mock.get_item(TableName=TABLE_NAME, Key={"user_id": {"S": str(user_id)}})


@patch("src.db.CLIENT")
@patch("src.db.TABLE_NAME", TABLE_NAME)
def test_given_notification_when_get_user_notification_then_user_returned(client_mock):

    user_id = "123"
    name = "Aitor"
    age = 30
    notified = True
    client_mock.get_item.return_value = {"Item": {"user_id": {"S": str(user_id)}, "name": {"S": name},
                                                  "age": {"N": str(age)}, "notified": {"BOOL": notified}}}

    assert db.get_user_notification(user_id) == {
        "user_id": user_id,
        "name": name,
        "age": age,
        "notified": notified
    }

    client_mock.get_item(TableName=TABLE_NAME, Key={"user_id": {"S": str(user_id)}})


@patch("src.db.CLIENT")
@patch("src.db.TABLE_NAME", TABLE_NAME)
def test_when_get_non_notified_then_only_non_notified_people_returned(client_mock):

    user_id1 = "123"
    name1 = "Aitor"
    age1 = 30
    user_id2 = "456"
    name2 = "Sergio"
    age2 = 25

    client_mock.get_paginator.return_value.paginate.return_value.build_full_result.return_value = \
        {"Items": [{"user_id": {"S": str(user_id1)}, "name": {"S": name1},
                    "age": {"N": str(age1)}, "notified": {"BOOL": True}},
                   {"user_id": {"S": str(user_id2)}, "name": {"S": name2},
                    "age": {"N": str(age2)}, "notified": {"BOOL": False}}
                   ]}

    assert db.get_non_notified_people() == [{
        "user_id": user_id2,
        "name": name2,
        "age": age2,
        "notified": False
    }]

    client_mock.get_paginator.assert_called_once_with('scan')
    client_mock.get_paginator.return_value.paginate.assert_called_once_with(TableName=TABLE_NAME)
    client_mock.get_paginator.return_value.paginate.return_value.build_full_result.assert_called_once_with()


@patch("src.db.CLIENT_SSM")
@patch("src.db.MIN_DATE_PARAMETER", "param_name")
def test_given_centres_and_last_update_when_save_min_date_info_then_info_stored_in_ssm(ssm_mock):
    centres_by_date = {
        datetime(2021, 3, 6): ["hosp1", "hosp2"],
        datetime(2021, 5, 9): ["hosp3", "hosp4"]
    }
    last_update = datetime.now()

    db.save_min_date_info(centres_by_date, last_update)

    ssm_mock.put_parameter.assert_called_once_with(Name=db.MIN_DATE_PARAMETER, Value=json.dumps({
        "updated_at": int(last_update.timestamp()),
        "centres_by_date": {
            "20210306": ["hosp1", "hosp2"],
            "20210509": ["hosp3", "hosp4"]
        }
    }), Overwrite=True, Type="String")


@patch("src.db.CLIENT_SSM")
@patch("src.db.MIN_DATE_PARAMETER", "param_name")
def test_given_no_parameter_when_save_min_date_info_then_empty_dict_and_none_returned(ssm_mock):
    ssm_mock.exceptions.ParameterNotFound = ParameterNotFound
    ssm_mock.get_parameter.side_effect = ParameterNotFound("error")

    centres_by_date, last_update = db.get_min_date_info()

    assert centres_by_date == {}
    assert last_update is None


@patch("src.db.CLIENT_SSM")
@patch("src.db.MIN_DATE_PARAMETER", "param_name")
def test_given_parameter_when_save_min_date_info_then_info_stored_in_ssm(ssm_mock):
    ssm_mock.exceptions.ParameterNotFound = ParameterNotFound
    last_update = datetime.now()
    ssm_mock.get_parameter.return_value = {
        "Parameter": {
            "Value": json.dumps({
                "updated_at": int(last_update.timestamp()),
                "centres_by_date": {
                    "20210306": ["hosp1", "hosp2"],
                    "20210509": ["hosp3", "hosp4"]
                }
            })
        }
    }

    centres_by_date, received_last_update = db.get_min_date_info()

    assert centres_by_date == {
        datetime(2021, 3, 6): ["hosp1", "hosp2"],
        datetime(2021, 5, 9): ["hosp3", "hosp4"]
    }
    assert received_last_update == datetime.fromtimestamp(int(last_update.timestamp()))


@patch("src.db.CLIENT_SSM")
@patch("src.db.get_min_years")
@patch("src.db.MIN_YEARS_PARAMETER", "param2_name")
def test_given_param_not_updated_when_save_min_years_then_put_parameter_called(get_min_years_mock, client_ssm_mock):
    years = 20
    get_min_years_mock.return_value = 21
    db.save_min_years(years)
    client_ssm_mock.put_parameter.assert_called_once_with(Name=db.MIN_YEARS_PARAMETER, Value=str(years),
                                                          Type="String")


@patch("src.db.CLIENT_SSM")
@patch("src.db.get_min_years")
@patch("src.db.MIN_YEARS_PARAMETER", "param2_name")
def test_given_param_not_updated_when_save_min_years_then_put_parameter_not_called(get_min_years_mock, client_ssm_mock):
    years = 21
    get_min_years_mock.return_value = 21
    db.save_min_years(years)
    client_ssm_mock.put_parameter.assert_not_called()


@patch("src.db.CLIENT_SSM")
@patch("src.db.MIN_YEARS_PARAMETER", "param2_name")
def test_given_param_exists_when_get_min_years_then_converted_param_returned(client_ssm_mock):
    years = "20"
    client_ssm_mock.exceptions.ParameterNotFound = ParameterNotFound
    client_ssm_mock.get_parameter.return_value = {
        "Parameter": {
            "Value": years
        }
    }

    assert db.get_min_years() == int(years)
    client_ssm_mock.get_parameter.assert_called_once_with(Name=db.MIN_YEARS_PARAMETER)


@patch("src.db.CLIENT_SSM")
@patch("src.db.MIN_YEARS_PARAMETER", "param2_name")
def test_given_param_does_not_exists_when_get_min_years_then_custom_exception_raises(client_ssm_mock):
    client_ssm_mock.exceptions.ParameterNotFound = ParameterNotFound
    client_ssm_mock.get_parameter.side_effect = ParameterNotFound

    with pytest.raises(ImpossibleToDetermineMaxAge):
        db.get_min_years()
