from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import hash_password, verify_password, create_access_token
from app.database.db import SessionLocal
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


# 🆕 cadastro
@router.post("/register")
def register(data: UserCreate):
    db = SessionLocal()

    user = db.query(User).filter(User.email == data.email).first()

    if user:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    new_user = User(
        email=data.email,
        password=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()

    return {"msg": "Usuário criado com sucesso"}


# 🔑 login
@router.post("/login")
def login(data: UserLogin):
    db = SessionLocal()

    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_access_token({"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }