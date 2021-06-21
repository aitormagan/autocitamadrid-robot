import boto3
import os
import json
from datetime import datetime

TABLE_NAME = os.environ.get("NOTIFICATIONS_TABLE")
CLIENT = boto3.client('dynamodb')
CLIENT_SSM = boto3.client('ssm')

__USER_ID = "user_id"
__NAME = "name"
__AGE = "age"
__NOTIFIED = "notified"

__MIN_DATE_PARAMETER = os.environ.get("PARAM_MIN_DATE")
__CENTRES_BY_DATE = "centres_by_date"
__UPDATED_AT = "updated_at"
__DATE_FORMAT = "%Y%m%d"


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


def save_min_date_info(centres_by_date, update_time):
    centres_by_date = {k.strftime(__DATE_FORMAT): v for k, v in centres_by_date.items()}
    CLIENT_SSM.put_parameter(Name=__MIN_DATE_PARAMETER, Value=json.dumps({
        "updated_at": int(update_time.timestamp()),
        "centres_by_date": centres_by_date
    }), Overwrite=True, Type="String")


def get_min_date_info():
    try:
        param_info = CLIENT_SSM.get_parameter(Name=__MIN_DATE_PARAMETER)
        decoded_content = json.loads(param_info["Parameter"]["Value"])
        centres_by_date = decoded_content[__CENTRES_BY_DATE]
        centres_by_date = {datetime.strptime(k, __DATE_FORMAT): v for k, v in centres_by_date.items()}
        return centres_by_date, datetime.fromtimestamp(decoded_content[__UPDATED_AT])
    except CLIENT_SSM.exceptions.ParameterNotFound:
        return {}, None
