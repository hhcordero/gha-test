# tests/test_aws_utils.py
import pytest
from botocore.exceptions import ClientError


def get_healthy_instances(instances: list[dict]) -> list[dict]:
    return [i for i in instances if i.get("state") == "running"]


def fetch_parameter(name: str, ssm_client) -> str:
    response = ssm_client.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]


# --- no mocking needed ---

def test_get_healthy_instances_returns_only_running():
    instances = [
        {"id": "i-001", "state": "running"},
        {"id": "i-002", "state": "stopped"},
        {"id": "i-003", "state": "running"},
    ]
    result = get_healthy_instances(instances)
    assert len(result) == 2
    assert all(i["state"] == "running" for i in result)


def test_get_healthy_instances_empty_input():
    assert get_healthy_instances([]) == []


# --- using mocker fixture (pytest-mock) ---

def test_fetch_parameter_returns_value(mocker):
    mock_ssm = mocker.MagicMock()
    mock_ssm.get_parameter.return_value = {
        "Parameter": {"Value": "my-secret-value"}
    }

    result = fetch_parameter("/myapp/db_password", mock_ssm)

    assert result == "my-secret-value"
    mock_ssm.get_parameter.assert_called_once_with(
        Name="/myapp/db_password", WithDecryption=True
    )


def test_fetch_parameter_propagates_client_error(mocker):
    mock_ssm = mocker.MagicMock()
    mock_ssm.get_parameter.side_effect = ClientError(
        {"Error": {"Code": "ParameterNotFound", "Message": "not found"}},
        "GetParameter",
    )

    with pytest.raises(ClientError):
        fetch_parameter("/does/not/exist", mock_ssm)
