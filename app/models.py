from sqlalchemy import Column, Integer, String, Float, DateTime
from .database.db import Base
from datetime import datetime


class Boleto(Base):
    __tablename__ = "boletos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True)
    beneficiario = Column(String)

    banco = Column(String)
    valor = Column(Float)
    risco = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)