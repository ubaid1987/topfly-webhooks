import datetime

import sentry_sdk
from fastapi import Depends, FastAPI, Form
from sqlalchemy.orm import Session

from config import Settings
from database import SessionLocal, engine
from models import Base, CompanySN
from services.topfly_service import TopflyService, Topflygeofence_create, Topflygeofence_delete
from utils.exception_handler import add_topfly_exception_handler
from utils.resp import TopflyResponse

setting = Settings()

Base.metadata.create_all(bind=engine)

sentry_sdk.init(
    dsn=setting.SENTRY_DNS,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
)

tags_metadata = [
    {
        "name": "Automatically Download Unit & Driver File",
        "description": "Send Download Command based on Unit & Driver File Availibility",
    },
    {
        "name": "Create Geofence",
        "description": "Create Geofence from Trailer",
    },
    {
        "name": "Delete Geofence",
        "description": "Delete Geofence from Trailer",
    },
]


app = FastAPI(
    title="Topfly App",
    description="Automatically download Driver and Unit Tachograph",
    version="1.2.1",
    contact={
        "name": "Muhammad Ubaid Ullah Khan",
        "email": "ubaidullah_khan@hotmail.com",
    },
    openapi_tags=tags_metadata,
)

add_topfly_exception_handler(app)


# Dependency
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/topfly-webhook/notification/", tags=["Automatically Download Unit & Driver File"])
def notification_webhook(
    unitId: str = Form(),
    driver: str = Form(),
    date: str = Form(),
    db: Session = Depends(get_db),
):
    sid = TopflyService.get_sid()
    service = TopflyService(sid, unitId, driver, None)
    bact = service.get_bact()
    mt_unit_epoch = service.get_unit_mt_epoch_time(unitId)
    c_code = service.get_driver_c_code()
    mt_epoch = service.get_mt_epoch_time(c_code, bact)

    if mt_unit_epoch == None:
        sn_value = service.get_value_from_company_card_api()
        company_sn = db.query(CompanySN).filter(
            CompanySN.sn == sn_value).first()
        if not company_sn:
            service.send_command()
            db.add(
                CompanySN(
                    sn=sn_value,
                    driver=driver,
                    unitId=unitId,
                )
            )
            db.commit()
        else:
            now = datetime.datetime.utcnow()
            trigger_diff = (now - company_sn.trigger_at).total_seconds() / 60
            if round(trigger_diff) > 30:
                service.send_command_tachigrafo()
                company_sn.trigger_at = now
                company_sn.driver = driver
                company_sn.unitId = unitId
                db.add(company_sn)
                db.commit()
                db.refresh(company_sn)
            else:
                return TopflyResponse(
                    data={
                        "trigger_at": str(company_sn.trigger_at),
                        "driver": company_sn.driver,
                        "unitId": company_sn.unitId,
                    },
                    message=f"A command already triggered at {company_sn.trigger_at} for driver {company_sn.driver}, unitId {company_sn.unitId}",
                )

        return TopflyResponse(message="Tachigrafo command has been triggered successfully.")

    if mt_unit_epoch != None and mt_epoch != None:
        mt_unit_utc_datetime = datetime.datetime.utcfromtimestamp(mt_unit_epoch)
        unit_now = datetime.datetime.utcnow()
        unit_days_difference = (unit_now - mt_unit_utc_datetime).days
        mt_utc_datetime = datetime.datetime.utcfromtimestamp(mt_epoch)
        now = datetime.datetime.utcnow()
        days_difference = (now - mt_utc_datetime).days
        if unit_days_difference < 60 and days_difference < 15:
            return TopflyResponse(message="Last modification time for unit is less than 60 days and for driver is less than 15 days")

        if unit_days_difference >= 60 and days_difference < 20:
            sn_value = service.get_value_from_company_card_api()
            company_sn = db.query(CompanySN).filter(
                CompanySN.sn == sn_value).first()
            if not company_sn:
                service.send_command()
                db.add(
                    CompanySN(
                        sn=sn_value,
                        driver=driver,
                        unitId=unitId,
                    )
                )
                db.commit()
            else:
                now = datetime.datetime.utcnow()
                trigger_diff = (
                    now - company_sn.trigger_at).total_seconds() / 60
                if round(trigger_diff) > 30:
                    service.send_command_tachigrafo()
                    company_sn.trigger_at = now
                    company_sn.driver = driver
                    company_sn.unitId = unitId
                    db.add(company_sn)
                    db.commit()
                    db.refresh(company_sn)
                else:
                    return TopflyResponse(
                        data={
                            "trigger_at": str(company_sn.trigger_at),
                            "driver": company_sn.driver,
                            "unitId": company_sn.unitId,
                        },
                        message=f"A command already triggered at {company_sn.trigger_at} for driver {company_sn.driver}, unitId {company_sn.unitId}",
                    )

            return TopflyResponse(message="Tachigrafo command has been triggered successfully.")

    sn_value = service.get_value_from_company_card_api()
    company_sn = db.query(CompanySN).filter(CompanySN.sn == sn_value).first()
    if not company_sn:
        service.send_command()
        db.add(
            CompanySN(
                sn=sn_value,
                driver=driver,
                unitId=unitId,
            )
        )
        db.commit()
    else:
        now = datetime.datetime.utcnow()
        trigger_diff = (now - company_sn.trigger_at).total_seconds() / 60
        if round(trigger_diff) > 30:
            service.send_command()
            company_sn.trigger_at = now
            company_sn.driver = driver
            company_sn.unitId = unitId
            db.add(company_sn)
            db.commit()
            db.refresh(company_sn)
        else:
            return TopflyResponse(
                data={
                    "trigger_at": str(company_sn.trigger_at),
                    "driver": company_sn.driver,
                    "unitId": company_sn.unitId,
                },
                message=f"A command already triggered at {company_sn.trigger_at} for driver {company_sn.driver}, unitId {company_sn.unitId}",
            )

    return TopflyResponse(message="Tessera command has been triggered successfully.")

@app.post("/topfly-geofence/create/", tags=["Create Geofence"])
def geofence_create(
    trailer: str = Form(),
    lon: str = Form(),
    lat: str = Form(),
):
    sid = Topflygeofence_create.get_sid()
    service = Topflygeofence_create(sid, trailer, lon, lat)
    bact = service.get_bact()
    data = service.create(bact)
    
    return TopflyResponse(data=data, message="Geofence has been created successfully.")


@app.post("/topfly-geofence/delete/", tags=["Delete Geofence"])
def geofence_delete(
    trailer: str = Form(),
):
    sid = Topflygeofence_delete.get_sid()
    service = Topflygeofence_delete(sid, trailer)
    bact = service.get_bact()
    geofence = service.get_geofence(bact)
    data = service.delete(bact, geofence)

    return TopflyResponse(data=data, message="Geofence has been deleted successfully.")
