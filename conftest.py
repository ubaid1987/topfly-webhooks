import pytest
from tests.topfly_api_responeses import SEND_COMMAND_API_RESPONSE


@pytest.fixture
def sid():
    return "02bb8a7dd9aaaf91dfc29ccba4c54201"


@pytest.fixture
def driver_name():
    return "Zaramella Andrea"


@pytest.fixture
def c_code():
    return "I100000165067000"


@pytest.fixture
def mt_epoch_time():
    return 1641042061  # Saturday, January 1, 2022 1:01:01 PM


@pytest.fixture
def company_card_sn():
    return "000FD0B7121704A5"


@pytest.fixture
def send_command_response():
    return SEND_COMMAND_API_RESPONSE
