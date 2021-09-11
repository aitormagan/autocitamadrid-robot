from unittest.mock import patch
import pytest
from src import db
from src.exceptions import ImpossibleToDetermineMaxAge


TABLE_NAME = "test-table"


class ParameterNotFound(BaseException):
    pass


@patch("src.db.CLIENT_SSM")
@patch("src.db.get_min_years")
@patch("src.db.MIN_YEARS_PARAMETER", "param2_name")
def test_given_param_not_updated_when_save_min_years_then_put_parameter_called(get_min_years_mock, client_ssm_mock):
    years = 20
    get_min_years_mock.return_value = 21
    db.save_min_years(years)
    client_ssm_mock.put_parameter.assert_called_once_with(Name=db.MIN_YEARS_PARAMETER, Value=str(years),
                                                          Type="String", Overwrite=True)


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
