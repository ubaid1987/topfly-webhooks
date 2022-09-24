from unittest.mock import Mock, patch

import pytest

from utils.exception_handler import TopflyException
from fastapi.exceptions import HTTPException

from config import Settings
from services.topfly_service import TopflyService
from tests.topfly_api_responeses import (
    COMPANY_CARD_API_RESPONSE,
    DRIVER_FILE_API_RESPONSE,
    INVALID_SID_RESPONSE,
    SEARCH_DRIVER_GROUP_ID_WITH_CODE_API_RESPONSE,
    TOKEN_LOGIN_API_INVALID_AUTH_TOKEN_RESPONSE,
    TOKEN_LOGIN_API_RESPONSE,
    TOKEN_LOGIN_API_WRONG_TOKEN_LENGTH_RESPONSE,
)

setting = Settings()


@patch("services.topfly_service.requests.get")
def test_get_sid_with_invalid_token(mock_get):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = (
        TOKEN_LOGIN_API_INVALID_AUTH_TOKEN_RESPONSE
    )

    with pytest.raises(TopflyException) as exc_info:
        TopflyService.get_sid()
    assert isinstance(exc_info.value, TopflyException)
    print("ehereeee........")
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.message
        == "TOKEN_LOGIN_API: Failed to get session id with reason INVALID_AUTH_TOKEN"
    )
    assert exc_info.value.data == TOKEN_LOGIN_API_INVALID_AUTH_TOKEN_RESPONSE


@patch("services.topfly_service.requests.get")
def test_get_sid_with_wrong_token_length(mock_get):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = (
        TOKEN_LOGIN_API_WRONG_TOKEN_LENGTH_RESPONSE
    )

    with pytest.raises(TopflyException) as exc_info:
        TopflyService.get_sid()
    assert isinstance(exc_info.value, TopflyException)
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.message
        == "TOKEN_LOGIN_API: Failed to get session id with reason WRONG_TOKEN_LENGTH"
    )
    assert exc_info.value.data == TOKEN_LOGIN_API_WRONG_TOKEN_LENGTH_RESPONSE


@patch("services.topfly_service.requests.get")
def test_get_sid(mock_get, sid):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = TOKEN_LOGIN_API_RESPONSE
    service = TopflyService("sid", "unitId", "driver", "date")
    assert service.get_sid() == sid


@patch("services.topfly_service.requests.get")
def test_get_driver_c_code(mock_get, driver_name):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = (
        SEARCH_DRIVER_GROUP_ID_WITH_CODE_API_RESPONSE
    )
    service = TopflyService("sid", "unitId", driver_name, "date")
    assert service.get_driver_c_code() == "I100000165067000"


@patch("services.topfly_service.requests.get")
def test_get_driver_c_code_with_invalid_sid(mock_get):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = INVALID_SID_RESPONSE

    from services.topfly_service import TopflyService

    service = TopflyService("invalid_sid", "unitId", "driver", "date")
    with pytest.raises(TopflyException) as exc_info:
        service.get_driver_c_code()
    assert isinstance(exc_info.value, TopflyException)
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.message
        == "SEARCH_DRIVER_GROUP_ID_WITH_CODE_API: Failed with error 1. Most likey beacuse of invalid sid"
    )
    assert exc_info.value.data == INVALID_SID_RESPONSE


@patch("services.topfly_service.requests.get")
def test_get_driver_c_code_with_invalid_driver_name(mock_get):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = (
        SEARCH_DRIVER_GROUP_ID_WITH_CODE_API_RESPONSE
    )

    service = TopflyService("sid", "unitId", "invalid_driver", "date")
    with pytest.raises(TopflyException) as exc_info:
        service.get_driver_c_code()
    assert isinstance(exc_info.value, TopflyException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.message == "No driver found with name invalid_driver"


@patch("services.topfly_service.requests.get")
def test_get_mt_epoch_time(mock_get, c_code):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = DRIVER_FILE_API_RESPONSE
    service = TopflyService("sid", "unitId", "driver_name", "date")
    assert service.get_mt_epoch_time(c_code) == 1663944440


@patch("services.topfly_service.requests.get")
def test_get_mt_epoch_time_with_invalid_sid(mock_get):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = INVALID_SID_RESPONSE

    service = TopflyService("invalid_sid", "unitId", "driver", "date")
    with pytest.raises(TopflyException) as exc_info:
        service.get_mt_epoch_time("c")
    assert isinstance(exc_info.value, TopflyException)
    assert exc_info.value.status_code == 400


@patch("services.topfly_service.requests.get")
def test_get_value_from_company_card_api(mock_get):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = COMPANY_CARD_API_RESPONSE
    service = TopflyService("sid", "unitId", "driver_name", "date")
    assert service.get_value_from_company_card_api() == "000FD0B7121704A5"


@patch("services.topfly_service.requests.get")
def test_get_value_from_company_card_api_with_invalid_sid(mock_get):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = INVALID_SID_RESPONSE

    service = TopflyService("invalid_sid", "unitId", "driver", "date")
    with pytest.raises(TopflyException) as exc_info:
        service.get_value_from_company_card_api()
    assert isinstance(exc_info.value, TopflyException)
    assert exc_info.value.status_code == 400
