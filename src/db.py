import boto3

TABLE_NAME = 'AutocitaMadridNotifications'
CLIENT = boto3.client('dynamodb')


def save_notification(user_id, age):
    CLIENT.put_item(TableName=TABLE_NAME, Item={"user_id": {"S": str(user_id)}, "age": {"N": str(age)}})


def delete_notification(user_id):
    CLIENT.delete_item(TableName=TABLE_NAME, Key={"user_id": {"S": str(user_id)}})