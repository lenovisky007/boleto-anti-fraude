from fastapi import APIRouter, Depends, Body, HTTPException
from pydantic import BaseModel

from app.auth import hash_password, verify_password, create_access_token
from app.database.db import SessionLocal
from app.models import User


router = APIRouter(prefix="/auth", tags=["Auth"])


# =========================
# MODELOS
# =========================
class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


# =========================
# REGISTER
# =========================
@router.post("/register")
def register(data: UserCreate = Body(...)):

    db = SessionLocal()

    user = db.query(User).filter(User.email == data.email).first()

    if user:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    new_user = User(
        email=data.email,
        password=hash_password(data.password),
        plan="free",
        requests_used=0
    )

    db.add(new_user)
    db.commit()

    return {
        "msg": "Usuário criado com sucesso"
    }


# =========================
# LOGIN
# =========================
@router.post("/login")
def login(data: UserLogin = Body(...)):

    db = SessionLocal()

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Senha inválida")

    token = create_access_token(
        {
            "sub": user.email,
            "plan": user.plan
        },
        expires_minutes=60  # 🔥 importante
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }