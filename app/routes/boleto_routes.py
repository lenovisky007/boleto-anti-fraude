from fastapi import APIRouter
from pydantic import BaseModel

from ..risk import analyze_boleto

router = APIRouter(prefix="/boleto", tags=["Boleto Antifraude"])


# =========================
# INPUT
# =========================
class BoletoRequest(BaseModel):
    codigo: str
    beneficiario: str | None = None


# =========================
# ENDPOINT PRINCIPAL
# =========================
@router.post("/validar")
def validar_boleto(data: BoletoRequest):

    resultado = analyze_boleto(
        raw_code=data.codigo,
        beneficiario=data.beneficiario
    )

    return {
        "status": "ok",
        "analise": resultado
    }