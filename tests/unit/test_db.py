from unittest.mock import patch, MagicMock
from src import db


@patch("src.db.CLIENT_SSM")
@patch("src.db.json")
@patch("src.db.THIRD_DOSE_INFO_PARAMETER", "param2_name")
def test_given_param_exists_when_get_min_years_then_converted_param_returned(json_mock, client_ssm_mock):
    parameter_value = MagicMock()
    client_ssm_mock.get_parameter.return_value = {
        "Parameter": {
            "Value": parameter_value
        }
    }

    assert db.get_info_third_dose() == json_mock.loads.return_value
    json_mock.loads.assert_called_once_with(parameter_value)
