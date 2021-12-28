import json
import os
import boto3

THIRD_DOSE_INFO_PARAMETER = os.environ.get("THIRD_DOSE_INFO_PARAMETER")
CLIENT = boto3.client('dynamodb')
CLIENT_SSM = boto3.client('ssm')

__USER_ID = "user_id"
__NAME = "name"
__AGE = "age"
__NOTIFIED = "notified"

__CENTRES_BY_DATE = "centres_by_date"
__UPDATED_AT = "updated_at"
__DATE_FORMAT = "%Y%m%d"


def get_info_third_dose():
    return json.loads(CLIENT_SSM.get_parameter(Name=THIRD_DOSE_INFO_PARAMETER)["Parameter"]["Value"])
