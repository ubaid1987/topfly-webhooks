from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from database import Base


class CompanySN(Base):
    __tablename__ = "company_sn"
    id = Column(Integer, primary_key=True, index=True)
    sn = Column(String)
    trigger_at = Column(DateTime, default=datetime.utcnow)
