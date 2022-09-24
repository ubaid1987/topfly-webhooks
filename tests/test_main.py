from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from main import app, get_db
from models import CompanySN

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


@pytest.fixture
def mock_get_sid(sid):
    with patch("services.topfly_service.TopflyService.get_sid", return_value=sid):
        yield


@pytest.fixture
def mock_get_driver_c_code(c_code):
    with patch(
        "services.topfly_service.TopflyService.get_driver_c_code", return_value=c_code
    ):
        yield


@pytest.fixture
def mock_get_mt_epoch_time(mt_epoch_time):
    with patch(
        "services.topfly_service.TopflyService.get_mt_epoch_time",
        return_value=mt_epoch_time,
    ):
        yield


@pytest.fixture
def mock_get_value_from_company_card_api(company_card_sn):
    with patch(
        "services.topfly_service.TopflyService.get_value_from_company_card_api",
        return_value=company_card_sn,
    ):
        yield


@pytest.fixture
def mock_send_command(send_command_response):
    with patch(
        "services.topfly_service.TopflyService.send_command",
        return_value=send_command_response,
    ):
        yield


@freeze_time("2022-01-30")
def test_notification_webhook(
    test_db,
    mock_get_sid,
    mock_get_driver_c_code,
    mock_get_mt_epoch_time,
    mock_get_value_from_company_card_api,
    mock_send_command,
):
    data = {
        "driver": "Zaramella Andrea",
        "unitId": 23149010,
        "date": "22.09.2022 19:15:56",
    }
    response = client.post("/topfly-webhook/notification/", data=data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Command has been triggered successfully"


@freeze_time("2022-01-02")
def test_notification_webhook_within_15_days(
    mock_get_sid,
    mock_get_driver_c_code,
    mock_get_mt_epoch_time,
    mock_get_value_from_company_card_api,
    sid,
):
    data = {
        "driver": "Zaramella Andrea",
        "unitId": 23149010,
        "date": "22.09.2022 19:15:56",
    }
    response = client.post("/topfly-webhook/notification/", data=data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "mt and current time difference is less 15 days"


@freeze_time("2022-01-30")
def test_notification_webhook_within_30_minutes(
    test_db,
    mock_get_sid,
    mock_get_driver_c_code,
    mock_get_mt_epoch_time,
    mock_get_value_from_company_card_api,
    company_card_sn,
    mock_send_command,
):
    db = TestingSessionLocal()
    db.add(
        CompanySN(
            sn=company_card_sn,
            driver="driver",
            unitId="unitId",
        )
    )
    db.commit()
    company_sn = db.query(CompanySN).first()
    data = {
        "driver": "Zaramella Andrea",
        "unitId": 23149010,
        "date": "22.09.2022 19:15:56",
    }
    response = client.post("/topfly-webhook/notification/", data=data)
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == {
        "trigger_at": str(company_sn.trigger_at),
        "driver": company_sn.driver,
        "unitId": company_sn.unitId,
    }


@freeze_time("2022-01-30")
def test_notification_webhook_after_30_minutes(
    test_db,
    mock_get_sid,
    mock_get_driver_c_code,
    mock_get_mt_epoch_time,
    mock_get_value_from_company_card_api,
    mock_send_command,
    company_card_sn,
):
    db = TestingSessionLocal()
    db.add(
        CompanySN(
            sn=company_card_sn,
            driver="driver",
            unitId="unitId",
            trigger_at=datetime.now() - timedelta(minutes=31),
        )
    )
    db.commit()
    data = {
        "driver": "Zaramella Andrea",
        "unitId": 23149010,
        "date": "22.09.2022 19:15:56",
    }
    response = client.post("/topfly-webhook/notification/", data=data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Command has been triggered successfully"
