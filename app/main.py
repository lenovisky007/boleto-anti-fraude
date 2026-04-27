from datetime import datetime
from typing import Optional
import re

from fastapi import FastAPI, HTTPException, Depends, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.database import SessionLocal, engine, Base
from app.models import User, AnalysisLog
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.risk import analyze_boleto
from app import models  # noqa: F401


app = FastAPI(title="Boleto Antifraude")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://boleto-anti-fraude.vercel.app",
        "https://boleto-anti-fraude-e26yba44q-lenovisky007s-projects.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options("/{rest_of_path:path}")
def options_handler(rest_of_path: str):
    return Response(status_code=200)


Base.metadata.create_all(bind=engine)


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AnalyzeRequest(BaseModel):
    linha_digitavel: str
    beneficiario: Optional[str] = ""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def limpar_linha(linha: str) -> str:
    return re.sub(r"\D", "", linha or "")


def identificar_banco(linha: str) -> str:
    bancos = {
        "001": "Banco do Brasil",
        "033": "Santander",
        "104": "Caixa Econômica Federal",
        "237": "Bradesco",
        "341": "Itaú",
        "380": "PicPay",
    }
    codigo = linha[:3] if linha else ""
    return bancos.get(codigo, "Desconhecido")


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")

    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    user_id = payload.get("user_id")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    return user


def get_current_month_usage(db: Session, user_id: int) -> int:
    return db.query(AnalysisLog).filter(
        AnalysisLog.user_id == user_id,
        extract("month", AnalysisLog.created_at) == datetime.utcnow().month,
        extract("year", AnalysisLog.created_at) == datetime.utcnow().year,
    ).count()


@app.get("/")
def home():
    return {"status": "API rodando 🚀"}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    used = get_current_month_usage(db, current_user.id)

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "plan": current_user.plan,
        "monthly_limit": current_user.monthly_limit,
        "used_this_month": used,
        "remaining": max(current_user.monthly_limit - used, 0),
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active,
    }


@app.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        plan="free",
        monthly_limit=10,
        is_admin=False,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Usuário criado com sucesso"}


@app.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    token = create_access_token({"user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@app.post("/analisar")
def analisar(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    used = get_current_month_usage(db, current_user.id)

    if used >= current_user.monthly_limit:
        raise HTTPException(status_code=403, detail="Limite atingido")

    linha = limpar_linha(payload.linha_digitavel)

    if not linha:
        raise HTTPException(status_code=400, detail="Linha digitável inválida")

    analise = analyze_boleto(linha, beneficiario=payload.beneficiario or "")

    db.add(AnalysisLog(user_id=current_user.id))
    db.commit()

    analise["banco"] = identificar_banco(linha)
    analise["used_this_month"] = used + 1
    analise["remaining"] = max(current_user.monthly_limit - (used + 1), 0)

    return analise