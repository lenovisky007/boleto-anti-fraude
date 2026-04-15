from datetime import datetime
from typing import Optional
import os
import re

from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import extract

from database import SessionLocal, engine, Base
from models import User, AnalysisLog, TrustedEntity
from auth import hash_password, verify_password, create_access_token, decode_access_token
from risk import analyze_boleto
from pdf_parser import extract_boleto_from_pdf


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois troque pelo seu domínio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# ============================================================
# MODELOS DE REQUEST
# ============================================================

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


class AdminChangePlanRequest(BaseModel):
    email: str
    plan: str
    monthly_limit: int


class AdminToggleUserStatusRequest(BaseModel):
    email: str
    is_active: bool


class BootstrapAdminRequest(BaseModel):
    email: str
    secret: str


class TrustedEntityCreateRequest(BaseModel):
    name: str
    type: str


# ============================================================
# HELPERS
# ============================================================

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
        "077": "Banco Inter",
        "104": "Caixa Econômica Federal",
        "121": "Agibank",
        "197": "Stone",
        "208": "BTG Pactual",
        "212": "Banco Original",
        "218": "Banco BS2",
        "237": "Bradesco",
        "260": "Nu Pagamentos / Nubank",
        "290": "PagBank / PagSeguro",
        "323": "Mercado Pago",
        "336": "C6 Bank",
        "341": "Itaú",
        "380": "PicPay",
        "422": "Safra",
        "461": "Asaas",
        "654": "Banco Digimais",
        "735": "Neon",
        "748": "Sicredi",
        "756": "Sicoob",
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
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return user


def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return current_user


def get_current_month_usage(db: Session, user_id: int) -> int:
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    used = db.query(AnalysisLog).filter(
        AnalysisLog.user_id == user_id,
        extract("month", AnalysisLog.created_at) == current_month,
        extract("year", AnalysisLog.created_at) == current_year
    ).count()

    return used


def load_dynamic_entities(db: Session):
    entities = db.query(TrustedEntity).all()

    beneficiarios = []
    keywords = []
    org_codes = []
    suspicious_terms = []

    for e in entities:
        if e.type == "beneficiario":
            beneficiarios.append(e.name)
        elif e.type == "keyword":
            keywords.append(e.name)
        elif e.type == "org_code":
            org_codes.append(e.name)
        elif e.type == "suspicious_term":
            suspicious_terms.append(e.name)

    return beneficiarios, keywords, org_codes, suspicious_terms


# ============================================================
# ROTAS PÚBLICAS / AUTH
# ============================================================

@app.get("/")
def home():
    return {"status": "API rodando 🚀"}


@app.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
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
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email
    password = payload.password

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
        "is_active": current_user.is_active
    }


# ============================================================
# ANÁLISE DE BOLETO
# ============================================================

@app.post("/analisar")
def analisar(payload: AnalyzeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    used = get_current_month_usage(db, current_user.id)

    if used >= current_user.monthly_limit:
        raise HTTPException(status_code=403, detail="Limite mensal atingido")

    linha_digitavel = limpar_linha(payload.linha_digitavel)
    beneficiario = payload.beneficiario or ""

    dynamic_beneficiarios, dynamic_keywords, dynamic_org_codes, dynamic_suspicious_terms = load_dynamic_entities(db)

    analise = analyze_boleto(
        linha_digitavel,
        beneficiario=beneficiario,
        dynamic_beneficiarios=dynamic_beneficiarios,
        dynamic_keywords=dynamic_keywords,
        dynamic_org_codes=dynamic_org_codes,
        dynamic_suspicious_terms=dynamic_suspicious_terms
    )

    log = AnalysisLog(user_id=current_user.id)
    db.add(log)
    db.commit()

    banco_nome = analise.get("banco_nome") or identificar_banco(linha_digitavel)

    return {
        **analise,
        "banco": banco_nome,
        "plan": current_user.plan,
        "used_this_month": used + 1,
        "remaining": max(current_user.monthly_limit - (used + 1), 0)
    }


@app.post("/analisar-pdf")
def analisar_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    used = get_current_month_usage(db, current_user.id)

    if used >= current_user.monthly_limit:
        raise HTTPException(status_code=403, detail="Limite mensal atingido")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF válido")

    parsed = extract_boleto_from_pdf(file.file)
    linha = parsed.get("linha_digitavel")

    if not linha:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível localizar uma linha digitável ou código de barras no PDF"
        )

    dynamic_beneficiarios, dynamic_keywords, dynamic_org_codes, dynamic_suspicious_terms = load_dynamic_entities(db)

    analise = analyze_boleto(
        linha,
        dynamic_beneficiarios=dynamic_beneficiarios,
        dynamic_keywords=dynamic_keywords,
        dynamic_org_codes=dynamic_org_codes,
        dynamic_suspicious_terms=dynamic_suspicious_terms
    )

    log = AnalysisLog(user_id=current_user.id)
    db.add(log)
    db.commit()

    banco_nome = analise.get("banco_nome") or identificar_banco(linha)

    return {
        **analise,
        "banco": banco_nome,
        "arquivo": file.filename,
        "metodo_extracao": parsed.get("metodo"),
        "linha_encontrada_no_pdf": linha,
        "plan": current_user.plan,
        "used_this_month": used + 1,
        "remaining": max(current_user.monthly_limit - (used + 1), 0)
    }


# ============================================================
# ROTAS ADMIN - USUÁRIOS
# ============================================================

@app.get("/admin/users")
def admin_list_users(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    result = []

    for user in users:
        used = get_current_month_usage(db, user.id)

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

    used = get_current_month_usage(db, user.id)

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
def admin_change_plan(payload: AdminChangePlanRequest, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.plan = payload.plan.strip()
    user.monthly_limit = int(payload.monthly_limit)

    db.commit()
    db.refresh(user)

    return {
        "message": "Plano atualizado com sucesso",
        "user": {
            "email": user.email,
            "plan": user.plan,
            "monthly_limit": user.monthly_limit
        }
    }


@app.post("/admin/toggle-user-status")
def admin_toggle_user_status(payload: AdminToggleUserStatusRequest, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = bool(payload.is_active)
    db.commit()
    db.refresh(user)

    return {
        "message": "Status do usuário atualizado com sucesso",
        "user": {
            "email": user.email,
            "is_active": user.is_active
        }
    }


# ============================================================
# ROTAS ADMIN - ENTIDADES CONFIÁVEIS / REGRAS
# ============================================================

@app.get("/admin/entities")
def admin_list_entities(
    entity_type: Optional[str] = None,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    query = db.query(TrustedEntity)

    if entity_type:
        query = query.filter(TrustedEntity.type == entity_type)

    entities = query.order_by(TrustedEntity.id.desc()).all()

    return [
        {
            "id": e.id,
            "name": e.name,
            "type": e.type,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in entities
    ]


@app.post("/admin/entities")
def admin_add_entity(
    payload: TrustedEntityCreateRequest,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    allowed_types = {"beneficiario", "keyword", "org_code", "suspicious_term"}

    entity_type = payload.type.strip().lower()
    name = payload.name.strip().lower()

    if entity_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipo inválido")

    if not name:
        raise HTTPException(status_code=400, detail="Nome inválido")

    existing = db.query(TrustedEntity).filter(
        TrustedEntity.name == name,
        TrustedEntity.type == entity_type
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Entidade já cadastrada")

    entity = TrustedEntity(
        name=name,
        type=entity_type
    )

    db.add(entity)
    db.commit()
    db.refresh(entity)

    return {
        "message": "Entidade adicionada com sucesso",
        "entity": {
            "id": entity.id,
            "name": entity.name,
            "type": entity.type
        }
    }


@app.delete("/admin/entities/{entity_id}")
def admin_delete_entity(
    entity_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    entity = db.query(TrustedEntity).filter(TrustedEntity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entidade não encontrada")

    db.delete(entity)
    db.commit()

    return {"message": "Entidade removida com sucesso"}


# ============================================================
# BOOTSTRAP ADMIN (TEMPORÁRIO)
# ============================================================

@app.post("/bootstrap-admin")
def bootstrap_admin(payload: BootstrapAdminRequest, db: Session = Depends(get_db)):
    expected_secret = os.getenv("BOOTSTRAP_ADMIN_SECRET", "minha_chave_admin_123456")

    if payload.secret != expected_secret:
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_admin = True
    user.is_active = True
    db.commit()
    db.refresh(user)

    return {"message": f"{payload.email} agora é admin"}