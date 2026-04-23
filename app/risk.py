from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Dict, Any

from app.data_loader import (
    KNOWN_LOW_RISK_BENEFICIARIES,
    CONCESSIONARIA_KEYWORDS,
    GOV_BENEFICIARY_KEYWORDS,
    KNOWN_PUBLIC_OR_SERVICE_CODES
)

# ============================================================
# BASES FIXAS
# ============================================================

COOPERATIVAS = {"085", "091", "097", "136", "748", "756"}

FINTECHS = {
    "077", "121", "197", "212", "218", "260",
    "290", "323", "336", "380", "461", "654", "735"
}

PSPS = {"197", "260", "290", "323", "336", "380", "461"}

GOV_BANK_HINTS = {"001", "104"}

SUSPICIOUS_TERMS = [
    "pagamento rapido",
    "financeiro urgente",
    "intermediador desconhecido",
    "conta teste",
    "beneficiario generico",
]

SEGMENTOS = {
    "1": "Prefeituras / Tributos",
    "2": "Saneamento",
    "3": "Energia / Gás",
    "4": "Telecom",
    "5": "Órgãos governamentais",
    "6": "Carnês / Serviços",
    "7": "Multas / Taxas",
    "8": "Convênios",
    "9": "Outros",
}

# ============================================================
# STRUCT
# ============================================================

@dataclass
class BoletoAnalysis:
    tipo: str
    linha: str
    barcode: str
    valido: bool
    banco_codigo: Optional[str]
    categoria: str
    risco: str
    score: int
    valor: Optional[float]
    vencimento: Optional[str]
    observacoes: list[str]


# ============================================================
# HELPERS
# ============================================================

def _digits(v: str) -> str:
    return re.sub(r"\D", "", v or "")


def _norm(v: str) -> str:
    return (v or "").lower().strip()


def modulo10(n: str) -> int:
    total, factor = 0, 2
    for d in reversed(n):
        add = int(d) * factor
        if add > 9:
            add = (add // 10) + (add % 10)
        total += add
        factor = 1 if factor == 2 else 2
    return (10 - total % 10) % 10


def modulo11(n: str) -> int:
    total, factor = 0, 2
    for d in reversed(n):
        total += int(d) * factor
        factor = 2 if factor == 9 else factor + 1
    dv = 11 - (total % 11)
    return 1 if dv in (0, 10, 11) else dv


def fator_to_date(f: str) -> Optional[str]:
    if not f.isdigit():
        return None
    base = date(1997, 10, 7)
    try:
        return (base + timedelta(days=int(f))).isoformat()
    except:
        return None


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

def categoria_banco(codigo: Optional[str]) -> str:
    if not codigo:
        return "desconhecido"
    if codigo in COOPERATIVAS:
        return "cooperativa"
    if codigo in FINTECHS:
        return "fintech"
    if codigo in PSPS:
        return "psp"
    return "banco"


def risco_label(score: int) -> str:
    if score <= 25:
        return "baixo"
    if score <= 55:
        return "medio"
    return "alto"


# ============================================================
# CORE
# ============================================================

def analyze_boleto(
    raw: str,
    beneficiario: Optional[str] = "",
    dynamic_beneficiarios: Optional[list[str]] = None,
    dynamic_keywords: Optional[list[str]] = None,
    dynamic_org_codes: Optional[list[str]] = None,
    dynamic_suspicious_terms: Optional[list[str]] = None
) -> Dict[str, Any]:

    linha = _digits(raw)
    beneficiario = _norm(beneficiario)
    obs = []

    if len(linha) not in (44, 47, 48):
        return {
            "tipo": "invalido",
            "risco": "alto",
            "score": 95,
            "mensagem": "Formato inválido",
            "observacoes": ["Tamanho incorreto"]
        }

    # ========================================================
    # BOLETO BANCÁRIO
    # ========================================================
    if linha.startswith(tuple(str(i).zfill(3) for i in range(1000))):

        barcode = linha if len(linha) == 44 else linha[:4] + linha[32] + linha[33:]

        banco = barcode[:3]
        categoria = categoria_banco(banco)

        valor = None
        if barcode[9:19].isdigit():
            valor = int(barcode[9:19]) / 100

        vencimento = fator_to_date(barcode[5:9])

        score = 0

        if categoria == "fintech":
            score += 25
            obs.append("Banco digital")

        if categoria == "psp":
            score += 30
            obs.append("Gateway pagamento")

        if not beneficiario:
            score += 10
            obs.append("Sem beneficiário")

        if any(t in beneficiario for t in SUSPICIOUS_TERMS):
            score += 20
            obs.append("Beneficiário suspeito")

        risco = risco_label(score)

        return {
            "tipo": "boleto",
            "linha": linha,
            "barcode": barcode,
            "banco_codigo": banco,
            "categoria": categoria,
            "risco": risco,
            "score": score,
            "valor": valor,
            "vencimento": vencimento,
            "observacoes": obs
        }

    # ========================================================
    # ARRECADAÇÃO
    # ========================================================
    if linha.startswith("8"):

        barcode = linha[:44]
        segmento = barcode[1]

        valor = None
        if barcode[4:15].isdigit():
            valor = int(barcode[4:15]) / 100

        score = 15

        if segmento not in SEGMENTOS:
            score += 15
            obs.append("Segmento desconhecido")

        if not beneficiario:
            score += 10

        risco = risco_label(score)

        return {
            "tipo": "arrecadacao",
            "linha": linha,
            "barcode": barcode,
            "segmento": segmento,
            "segmento_desc": SEGMENTOS.get(segmento),
            "risco": risco,
            "score": score,
            "valor": valor,
            "observacoes": obs
        }

    # ========================================================
    # FALLBACK
    # ========================================================
    return {
        "tipo": "desconhecido",
        "risco": "alto",
        "score": 90,
        "mensagem": "Não reconhecido",
        "observacoes": ["Estrutura fora do padrão"]
    }