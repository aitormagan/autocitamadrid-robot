import boto3
import os

TABLE_NAME = os.environ.get("NOTIFICATIONS_TABLE")
CLIENT = boto3.client('dynamodb')

__USER_ID = "user_id"
__NAME = "name"
__AGE = "age"
__NOTIFIED = "notified"


def save_notification(user_id, name, age, notified=False):
    CLIENT.put_item(TableName=TABLE_NAME, Item={__USER_ID: {"S": str(user_id)}, __NAME: {"S": name},
                                                __AGE: {"N": str(age)}, __NOTIFIED: {"BOOL": notified}})


def delete_notification(user_id):
    CLIENT.delete_item(TableName=TABLE_NAME, Key={__USER_ID: {"S": str(user_id)}})


def get_user_notification(user_id):
    item = CLIENT.get_item(TableName=TABLE_NAME, Key={__USER_ID: {"S": str(user_id)}}).get("Item", None)
    return __parse_item(item) if item else None


def get_non_notified_people():
    paginator = CLIENT.get_paginator('scan')
    dynamo_items = paginator.paginate(TableName=TABLE_NAME).build_full_result().get("Items", [])
    non_notified = []

    for item in dynamo_items:
        if not item.get(__NOTIFIED).get("BOOL"):
            non_notified.append(__parse_item(item))

    return non_notified


def __parse_item(item):
    return {
        "name": item[__NAME]["S"],
        "age": int(item[__AGE]["N"]),
        "user_id": item[__USER_ID]["S"],
        "notified": item[__NOTIFIED]["BOOL"]
    }