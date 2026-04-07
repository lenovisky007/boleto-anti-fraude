from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import datetime
import re

from database import SessionLocal, engine, Base
from models import User, AnalysisLog
from auth import hash_password, verify_password, create_access_token, decode_access_token

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois troque pelo seu domínio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def limpar_linha(linha: str) -> str:
    return re.sub(r"\D", "", linha)


def identificar_banco(linha: str) -> str:
    bancos = {
        "001": "Banco do Brasil",
        "104": "Caixa",
        "237": "Bradesco",
        "341": "Itaú",
    }
    return bancos.get(linha[:3], "Desconhecido")


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return user


def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return current_user


@app.get("/")
def home():
    return {"status": "API rodando 🚀"}


@app.post("/register")
def register(payload: dict, db: Session = Depends(get_db)):
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")

    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Preencha nome, email e senha")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        plan="free",
        monthly_limit=10,
        is_admin=False,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Usuário criado com sucesso"}


@app.post("/login")
def login(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email")
    password = payload.get("password")

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    token = create_access_token({"user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "plan": user.plan,
            "monthly_limit": user.monthly_limit,
            "is_admin": user.is_admin,
            "is_active": user.is_active
        }
    }


@app.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    used = db.query(AnalysisLog).filter(
        AnalysisLog.user_id == current_user.id,
        extract("month", AnalysisLog.created_at) == current_month,
        extract("year", AnalysisLog.created_at) == current_year
    ).count()

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "plan": current_user.plan,
        "monthly_limit": current_user.monthly_limit,
        "used_this_month": used,
        "remaining": max(current_user.monthly_limit - used, 0),
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active
    }


@app.post("/analisar")
def analisar(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    used = db.query(AnalysisLog).filter(
        AnalysisLog.user_id == current_user.id,
        extract("month", AnalysisLog.created_at) == current_month,
        extract("year", AnalysisLog.created_at) == current_year
    ).count()

    if used >= current_user.monthly_limit:
        raise HTTPException(status_code=403, detail="Limite mensal atingido")

    linha_digitavel = payload.get("linha_digitavel", "")
    linha = limpar_linha(linha_digitavel)
    banco = identificar_banco(linha)

    log = AnalysisLog(user_id=current_user.id)
    db.add(log)
    db.commit()

    return {
        "banco": banco,
        "linha": linha,
        "plan": current_user.plan,
        "used_this_month": used + 1,
        "remaining": max(current_user.monthly_limit - (used + 1), 0)
    }


@app.get("/admin/users")
def admin_list_users(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).all()

    result = []
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    for user in users:
        used = db.query(AnalysisLog).filter(
            AnalysisLog.user_id == user.id,
            extract("month", AnalysisLog.created_at) == current_month,
            extract("year", AnalysisLog.created_at) == current_year
        ).count()

        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "plan": user.plan,
            "monthly_limit": user.monthly_limit,
            "used_this_month": used,
            "remaining": max(user.monthly_limit - used, 0),
            "is_admin": user.is_admin,
            "is_active": user.is_active
        })

    return result


@app.get("/admin/user-by-email")
def admin_get_user_by_email(email: str, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    used = db.query(AnalysisLog).filter(
        AnalysisLog.user_id == user.id,
        extract("month", AnalysisLog.created_at) == current_month,
        extract("year", AnalysisLog.created_at) == current_year
    ).count()

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "plan": user.plan,
        "monthly_limit": user.monthly_limit,
        "used_this_month": used,
        "remaining": max(user.monthly_limit - used, 0),
        "is_admin": user.is_admin,
        "is_active": user.is_active
    }


@app.post("/admin/change-plan")
def admin_change_plan(payload: dict, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    email = payload.get("email")
    plan = payload.get("plan")
    monthly_limit = payload.get("monthly_limit")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if not plan or monthly_limit is None:
        raise HTTPException(status_code=400, detail="Informe plano e limite mensal")

    user.plan = plan
    user.monthly_limit = int(monthly_limit)

    db.commit()

    return {"message": "Plano atualizado com sucesso"}


@app.post("/admin/toggle-user-status")
def admin_toggle_user_status(payload: dict, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    email = payload.get("email")
    is_active = payload.get("is_active")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = bool(is_active)
    db.commit()

    return {"message": "Status do usuário atualizado com sucesso"}
import os
@app.post("/bootstrap-admin")
def bootstrap_admin(payload: dict, db: Session = Depends(get_db)):
    secret = payload.get("secret")
    email = payload.get("email")

    expected_secret = os.getenv("BOOTSTRAP_ADMIN_SECRET")

    if not expected_secret or secret != expected_secret:
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_admin = True
    user.is_active = True
    db.commit()

    return {"message": f"{email} agora é admin"}