from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    plan = Column(String, default="free")
    is_admin = Column(Boolean, default=False)
    token = Column(String, unique=True)