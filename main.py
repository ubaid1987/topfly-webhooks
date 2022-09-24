import datetime

import requests
from fastapi import Depends, FastAPI, Form
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, CompanySN
from services.topfly_service import TopflyService

Base.metadata.create_all(bind=engine)
app = FastAPI()

# Dependency
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/topfly-webhook/notification/")
def notification_webhook(
    unitId: str = Form(),
    driver: str = Form(),
    date: str = Form(),
    db: Session = Depends(get_db),
):
    sid = TopflyService.get_sid()
    service = TopflyService(sid, unitId, driver, None)
    c_code = service.get_driver_c_code()
    mt_epoch = service.get_mt_epoch_time(c_code)
    mt_utc_datetime = datetime.datetime.utcfromtimestamp(mt_epoch)
    now = datetime.datetime.utcnow()
    days_difference = (now - mt_utc_datetime).days
    if days_difference < 15:
        return {"message": "mt and current time difference is less 15 days"}
    sn_value = service.get_value_from_company_card_api()
    company_sn = db.query(CompanySN).filter(CompanySN.sn == sn_value).first()
    if not company_sn:
        service.send_command()
        db.add(CompanySN(sn=sn_value))
        db.commit()
    else:
        now = datetime.datetime.utcnow()
        trigger_diff = (now - company_sn.trigger_at).total_seconds() / 60
        if round(trigger_diff) > 30:
            service.send_command()
            company_sn.trigger_at = now
            db.add(company_sn)
            db.commit()
            db.refresh(company_sn)

    return {"message": "Command has been triggered successfully"}
