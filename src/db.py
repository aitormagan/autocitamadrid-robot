import boto3
import os
import json
from datetime import datetime
from src.exceptions import ImpossibleToDetermineMaxAge

TABLE_NAME = os.environ.get("NOTIFICATIONS_TABLE")
MIN_DATE_PARAMETER = os.environ.get("PARAM_MIN_DATE")
MIN_YEARS_PARAMETER = os.environ.get("PARAM_MIN_YEARS")
CLIENT = boto3.client('dynamodb')
CLIENT_SSM = boto3.client('ssm')

__USER_ID = "user_id"
__NAME = "name"
__AGE = "age"
__NOTIFIED = "notified"

__CENTRES_BY_DATE = "centres_by_date"
__UPDATED_AT = "updated_at"
__DATE_FORMAT = "%Y%m%d"


def save_min_years(max_years):
    try:
        current_years = get_min_years()
    except ImpossibleToDetermineMaxAge:
        current_years = None

    if current_years != max_years:
        CLIENT_SSM.put_parameter(Name=MIN_YEARS_PARAMETER, Value=str(max_years), Type="String", Overwrite=True)


def get_min_years():
    try:
        return int(CLIENT_SSM.get_parameter(Name=MIN_YEARS_PARAMETER)["Parameter"]["Value"])
    except CLIENT_SSM.exceptions.ParameterNotFound:
        raise ImpossibleToDetermineMaxAge()
