from sqlalchemy import Column, Integer, String
from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    email = Column(String, unique=True, index=True)
    password = Column(String)

    plan = Column(String, default="free")
    requests_used = Column(Integer, default=0)