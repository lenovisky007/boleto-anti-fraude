from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.routes.auth_routes import router as auth_router
from app.dependencies.auth_guard import get_current_user
from app.risk import calculate_risk

app = FastAPI(title="Painel admin")
app.include_router(auth_router)

# =========================
# 🔥 CORS CORRIGIDO
# =========================
origins = [
    "https://boleto-anti-fraude.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 🔥 GARANTE RESPOSTA AO PREFLIGHT (CRÍTICO)
# =========================
@app.options("/{rest_of_path:path}")
def preflight_handler(rest_of_path: str):
    return Response(status_code=200)


# =========================
# ROTAS
# =========================
app.include_router(auth_router)

# =========================
# MODELO
# =========================
class BoletoRequest(BaseModel):
    codigo: str
    beneficiario: str | None = None


# =========================
# ENDPOINTS
# =========================
@app.get("/")
def home():
    return {"status": "online"}


@app.get("/status")
def status():
    return {"api": "ok"}


@app.post("/validar-boleto")
def validar(data: BoletoRequest, user=Depends(get_current_user)):
    result = calculate_risk(
        raw_code=data.codigo,
        beneficiario=data.beneficiario
    )

    return {
        "user": user.get("sub"),
        "result": result
    }