from fastapi import FastAPI, Depends
from pydantic import BaseModel

from app.routes.auth_routes import router as auth_router
from app.dependencies.auth_guard import get_current_user
from app.risk import calculate_risk

app = FastAPI(title="SaaS Antifraude")

app.include_router(auth_router)


# =========================
# MODELO
# =========================
class BoletoRequest(BaseModel):
    codigo: str
    beneficiario: str | None = None


# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Boleto Antifraude SaaS 🚀"
    }


# =========================
# VALIDAR (PROTEGIDO)
# =========================
@app.post("/validar-boleto")
def validar(data: BoletoRequest, user=Depends(get_current_user)):

    result = calculate_risk(
        raw_code=data.codigo,
        beneficiario=data.beneficiario
    )

    return {
        "user": user,
        "result": result
    }


# =========================
# STATUS PÚBLICO
# =========================
@app.get("/status")
def status():
    return {
        "api": "ok",
        "auth": "enabled"
    }