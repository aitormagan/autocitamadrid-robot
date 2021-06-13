import boto3

TABLE_NAME = 'AutocitaMadridNotifications'
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


def get_non_notified_people():
    paginator = CLIENT.get_paginator('scan')
    dynamo_items = paginator.paginate(TableName=TABLE_NAME).build_full_result().get("Items", [])
    non_notified = []

    for item in dynamo_items:
        if not item.get(__NOTIFIED).get("BOOL"):
            non_notified.append({
                "name": item[__NAME]["S"],
                "age": int(item[__AGE]["N"]),
                "user_id": item[__USER_ID]["S"]
            })

    return non_notified
