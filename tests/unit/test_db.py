from unittest.mock import patch, MagicMock
from src import db


TABLE_NAME = "test-table"


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



