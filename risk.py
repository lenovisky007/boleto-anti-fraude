from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Dict, Any

from data_loader import (
    KNOWN_LOW_RISK_BENEFICIARIES,
    CONCESSIONARIA_KEYWORDS,
    GOV_BENEFICIARY_KEYWORDS,
    KNOWN_PUBLIC_OR_SERVICE_CODES
)


# ============================================================
# BASES FIXAS DE INSTITUIÇÕES
# ============================================================

BANCOS_TRADICIONAIS = {
    "001": "Banco do Brasil",
    "003": "Banco da Amazônia",
    "004": "Banco do Nordeste do Brasil",
    "021": "Banestes",
    "024": "Banco Bandepe",
    "025": "Banco Alfa",
    "029": "Banco Itaú Consignado",
    "033": "Santander",
    "036": "Banco Bradesco BBI",
    "037": "Banpará",
    "041": "Banrisul",
    "047": "Banese",
    "060": "Travelex / Confidence",
    "062": "Hipercard Banco Múltiplo",
    "063": "Banco Bradescard",
    "064": "Goldman Sachs do Brasil",
    "065": "Banco Andbank",
    "066": "Banco Morgan Stanley",
    "069": "Crefisa",
    "070": "BRB",
    "074": "Banco J. Safra",
    "075": "Banco ABN Amro",
    "076": "Banco KDB",
    "077": "Banco Inter",
    "082": "Banco Topázio",
    "083": "Banco da China Brasil",
    "084": "Uniprime",
    "085": "Ailos / Cecred",
    "091": "Cresol",
    "094": "Banco Finaxis",
    "095": "Travelex Banco de Câmbio",
    "096": "B3 / BM&FBovespa Serviços Financeiros",
    "097": "Credisis",
    "104": "Caixa Econômica Federal",
    "107": "Banco BOCOM BBM",
    "121": "Agibank",
    "136": "Unicred",
    "149": "Facta Financeira",
    "157": "ICBC do Brasil",
    "169": "Banco Olé",
    "184": "Banco Itaú BBA",
    "197": "Stone",
    "208": "BTG Pactual",
    "212": "Banco Original",
    "217": "Banco John Deere",
    "218": "Banco BS2",
    "222": "Banco Crédit Agricole Brasil",
    "224": "Banco Fibra",
    "233": "Banco Cifra",
    "237": "Bradesco",
    "241": "Banco Clássico",
    "243": "Banco Máxima",
    "246": "Banco ABC Brasil",
    "254": "Paraná Banco",
    "260": "Nu Pagamentos / Nubank",
    "263": "Banco Cacique",
    "265": "Banco Fator",
    "266": "Banco Cédula",
    "290": "PagBank / PagSeguro Banco",
    "300": "Banco de La Nacion Argentina",
    "318": "Banco BMG",
    "320": "Banco Industrial do Brasil",
    "323": "Mercado Pago",
    "336": "C6 Bank",
    "341": "Itaú Unibanco",
    "366": "Banco Société Générale Brasil",
    "370": "Banco Mizuho",
    "376": "Banco J.P. Morgan",
    "380": "PicPay",
    "389": "Banco Mercantil do Brasil",
    "394": "Banco Bradesco Financiamentos",
    "412": "Banco Capital",
    "422": "Banco Safra",
    "456": "Banco MUFG Brasil",
    "461": "Asaas",
    "464": "Banco Sumitomo Mitsui Brasileiro",
    "473": "Banco Caixa Geral Brasil",
    "479": "Banco Itaubank",
    "487": "Deutsche Bank Brasil",
    "492": "ING Bank",
    "495": "Banco Provincia de Buenos Aires",
    "505": "Banco Credit Suisse Brasil",
    "600": "Banco Luso Brasileiro",
    "604": "Banco Industrial do Brasil",
    "610": "Banco VR",
    "611": "Banco Paulista",
    "612": "Banco Guanabara",
    "613": "Banco Pecúnia",
    "623": "Banco Pan",
    "626": "Banco C6 Consignado / estrutura relacionada",
    "630": "Banco Smartbank",
    "633": "Banco Rendimento",
    "634": "Banco Triângulo",
    "637": "Banco Sofisa",
    "643": "Banco Pine",
    "652": "Itaú Unibanco Holding / estrutura específica",
    "653": "Banco Indusval",
    "654": "Banco Digimais",
    "655": "Banco Votorantim",
    "707": "Banco Daycoval",
    "712": "Banco Ourinvest",
    "735": "Neon / estrutura operacional varia",
    "739": "Banco Cetelem",
    "741": "Banco Ribeirão Preto",
    "743": "Banco Semear",
    "745": "Citibank",
    "746": "Banco Modal",
    "747": "Banco Rabobank",
    "748": "Sicredi",
    "751": "Scotiabank Brasil",
    "752": "BNP Paribas Brasil",
    "756": "Sicoob",
}

COOPERATIVAS = {
    "085": "Ailos / Cecred",
    "091": "Cresol",
    "097": "Credisis",
    "136": "Unicred",
    "748": "Sicredi",
    "756": "Sicoob",
}

FINTECHS_E_DIGITAIS = {
    "077": "Banco Inter",
    "121": "Agibank",
    "197": "Stone",
    "212": "Banco Original",
    "218": "Banco BS2",
    "260": "Nu Pagamentos / Nubank",
    "290": "PagBank / PagSeguro Banco",
    "323": "Mercado Pago",
    "336": "C6 Bank",
    "380": "PicPay",
    "461": "Asaas",
    "654": "Banco Digimais",
    "735": "Neon",
    "746": "Banco Modal",
}

PSPS_E_GATEWAYS = {
    "197": "Stone",
    "260": "Nu Pagamentos",
    "290": "PagBank / PagSeguro",
    "323": "Mercado Pago",
    "336": "C6 Bank",
    "380": "PicPay",
    "461": "Asaas",
}

GOV_BANK_HINTS = {"001", "104"}

SUSPICIOUS_BENEFICIARY_TERMS = [
    "pagamento rápido",
    "pagamento rapido",
    "financeiro urgente",
    "intermediador desconhecido",
    "conta teste",
    "beneficiário genérico",
    "beneficiario generico",
]

SEGMENTOS_ARRECADACAO = {
    "1": "Prefeituras / Governo / Taxas / Tributos",
    "2": "Saneamento",
    "3": "Energia elétrica / Gás",
    "4": "Telecomunicações",
    "5": "Órgãos governamentais / arrecadação pública",
    "6": "Carnês / Serviços / Convênios",
    "7": "Multas / Taxas / Serviços diversos",
    "8": "Uso reservado / Convênios",
    "9": "Outros serviços / Convênios",
}


# ============================================================
# ESTRUTURA DE SAÍDA
# ============================================================

@dataclass
class BoletoAnalysis:
    tipo: str
    formato_entrada: str
    linha_normalizada: str
    barcode_44: str
    valido_estrutura: bool
    valido_dv_campos: bool
    valido_dv_geral: bool
    banco_codigo: Optional[str]
    banco_nome: str
    categoria: str
    risco: str
    score: int
    mensagem: str
    valor: Optional[float]
    vencimento: Optional[str]
    observacoes: list[str]
    segmento: Optional[str]
    segmento_descricao: Optional[str]
    empresa_orgao_codigo: Optional[str]


# ============================================================
# FUNÇÕES BÁSICAS
# ============================================================

def _only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def modulo10(number: str) -> int:
    total = 0
    factor = 2
    for n in reversed(number):
        add = int(n) * factor
        if add > 9:
            add = (add // 10) + (add % 10)
        total += add
        factor = 1 if factor == 2 else 2
    dv = (10 - (total % 10)) % 10
    return dv


def modulo11_boleto(number: str) -> int:
    total = 0
    factor = 2
    for n in reversed(number):
        total += int(n) * factor
        factor += 1
        if factor > 9:
            factor = 2
    remainder = total % 11
    dv = 11 - remainder
    if dv in (0, 10, 11):
        return 1
    return dv


def modulo11_arrecadacao(number: str) -> int:
    total = 0
    factor = 2
    for n in reversed(number):
        total += int(n) * factor
        factor += 1
        if factor > 9:
            factor = 2
    remainder = total % 11
    dv = 11 - remainder
    if dv in (0, 1, 10, 11):
        return 0
    return dv


def fator_vencimento_to_date(fator: str) -> Optional[date]:
    if not fator.isdigit():
        return None

    value = int(fator)
    if value == 0:
        return None

    base = date(1997, 10, 7)
    try:
        return base + timedelta(days=value)
    except Exception:
        return None


# ============================================================
# BOLETO BANCÁRIO
# ============================================================

def is_boleto_bancario_barcode44(code: str) -> bool:
    return len(code) == 44 and code[:3].isdigit() and code[3] == "9"


def is_boleto_bancario_linha47(code: str) -> bool:
    return len(code) == 47 and code[:3].isdigit() and code[3] == "9"


def linha47_to_barcode44(linha: str) -> str:
    dv_geral = linha[32]
    campo5 = linha[33:47]

    banco_moeda = linha[0:4]
    livre_1 = linha[4:9]
    livre_2 = linha[10:20]
    livre_3 = linha[21:31]

    return banco_moeda + dv_geral + campo5 + livre_1 + livre_2 + livre_3


def validar_campos_linha47(linha: str) -> bool:
    campo1 = linha[0:9]
    dv1 = int(linha[9])

    campo2 = linha[10:20]
    dv2 = int(linha[20])

    campo3 = linha[21:31]
    dv3 = int(linha[31])

    return (
        modulo10(campo1) == dv1 and
        modulo10(campo2) == dv2 and
        modulo10(campo3) == dv3
    )


def validar_dv_geral_barcode44_cobranca(barcode: str) -> bool:
    body = barcode[:4] + barcode[5:]
    dv_real = int(barcode[4])
    dv_calc = modulo11_boleto(body)
    return dv_real == dv_calc


def extrair_valor_e_vencimento_cobranca(barcode: str) -> tuple[Optional[float], Optional[str]]:
    fator = barcode[5:9]
    valor_str = barcode[9:19]

    valor = None
    vencimento = None

    if valor_str.isdigit():
        valor = int(valor_str) / 100

    dt = fator_vencimento_to_date(fator)
    if dt:
        vencimento = dt.isoformat()

    return valor, vencimento


# ============================================================
# ARRECADAÇÃO / CONVÊNIOS
# ============================================================

def is_arrecadacao_barcode44(code: str) -> bool:
    return len(code) == 44 and code[0] == "8"


def is_arrecadacao_linha48(code: str) -> bool:
    return len(code) == 48 and code[0] == "8"


def linha48_to_barcode44(linha: str) -> str:
    blocos = [linha[i:i+12] for i in range(0, 48, 12)]
    dados = [b[:11] for b in blocos]
    return "".join(dados)


def arrecadacao_usa_modulo10(barcode44: str) -> bool:
    return barcode44[2] in {"6", "7"}


def validar_campos_linha48(linha: str) -> bool:
    blocos = [linha[i:i+12] for i in range(0, 48, 12)]
    barcode44 = linha48_to_barcode44(linha)
    usa_mod10 = arrecadacao_usa_modulo10(barcode44)

    for bloco in blocos:
        dados = bloco[:11]
        dv_real = int(bloco[11])
        dv_calc = modulo10(dados) if usa_mod10 else modulo11_arrecadacao(dados)
        if dv_real != dv_calc:
            return False
    return True


def validar_dv_geral_barcode44_arrecadacao(barcode: str) -> bool:
    body = barcode[:3] + barcode[4:]
    dv_real = int(barcode[3])
    usa_mod10 = arrecadacao_usa_modulo10(barcode)
    dv_calc = modulo10(body) if usa_mod10 else modulo11_arrecadacao(body)
    return dv_real == dv_calc


def extrair_valor_arrecadacao(barcode: str) -> Optional[float]:
    valor_ref = barcode[2]
    valor_str = barcode[4:15]

    if valor_ref in {"6", "7", "8", "9"} and valor_str.isdigit():
        return int(valor_str) / 100

    return None


def extrair_segmento_arrecadacao(barcode: str) -> tuple[Optional[str], Optional[str]]:
    if len(barcode) != 44 or barcode[0] != "8":
        return None, None

    segmento = barcode[1]
    return segmento, SEGMENTOS_ARRECADACAO.get(segmento, "Segmento não mapeado")


def extrair_empresa_orgao_codigo(barcode: str) -> Optional[str]:
    if len(barcode) != 44 or barcode[0] != "8":
        return None

    return barcode[15:19]


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

def get_categoria_por_codigo(codigo: Optional[str]) -> tuple[str, str]:
    if not codigo:
        return "desconhecido", "Desconhecido"

    if codigo in COOPERATIVAS:
        return "cooperativa", COOPERATIVAS[codigo]

    if codigo in FINTECHS_E_DIGITAIS:
        return "fintech_ou_digital", FINTECHS_E_DIGITAIS[codigo]

    if codigo in PSPS_E_GATEWAYS:
        return "psp_ou_gateway", PSPS_E_GATEWAYS[codigo]

    if codigo in BANCOS_TRADICIONAIS:
        return "banco_tradicional", BANCOS_TRADICIONAIS[codigo]

    return "desconhecido", "Desconhecido"


def looks_government_like(beneficiario: Optional[str], banco_codigo: Optional[str], tipo: str) -> bool:
    beneficiario_norm = _normalize_text(beneficiario)

    if any(k in beneficiario_norm for k in GOV_BENEFICIARY_KEYWORDS):
        return True

    if tipo == "arrecadacao" and banco_codigo in GOV_BANK_HINTS:
        return True

    return False


def is_known_low_risk_beneficiary(
    beneficiario: Optional[str],
    dynamic_beneficiarios: Optional[list[str]] = None
) -> bool:
    beneficiario_norm = _normalize_text(beneficiario)
    dynamic_beneficiarios = dynamic_beneficiarios or []
    all_items = list(KNOWN_LOW_RISK_BENEFICIARIES) + list(dynamic_beneficiarios)
    return any(k in beneficiario_norm for k in all_items)


def looks_concessionaria_like(
    beneficiario: Optional[str],
    dynamic_keywords: Optional[list[str]] = None
) -> bool:
    beneficiario_norm = _normalize_text(beneficiario)
    dynamic_keywords = dynamic_keywords or []
    all_items = list(CONCESSIONARIA_KEYWORDS) + list(dynamic_keywords)
    return any(k in beneficiario_norm for k in all_items)


def looks_suspicious_beneficiary(
    beneficiario: Optional[str],
    dynamic_suspicious_terms: Optional[list[str]] = None
) -> bool:
    beneficiario_norm = _normalize_text(beneficiario)
    dynamic_suspicious_terms = dynamic_suspicious_terms or []
    all_items = list(SUSPICIOUS_BENEFICIARY_TERMS) + list(dynamic_suspicious_terms)
    return any(k in beneficiario_norm for k in all_items)


def empresa_orgao_parece_confiavel(
    codigo: Optional[str],
    dynamic_org_codes: Optional[list[str]] = None
) -> bool:
    if not codigo:
        return False
    dynamic_org_codes = dynamic_org_codes or []
    return codigo in KNOWN_PUBLIC_OR_SERVICE_CODES or codigo in dynamic_org_codes


# ============================================================
# MOTOR DE RISCO
# ============================================================

def score_to_label(score: int) -> str:
    if score <= 25:
        return "baixo"
    if score <= 55:
        return "medio"
    return "alto"


def analyze_boleto(
    raw_code: str,
    beneficiario: Optional[str] = None,
    dynamic_beneficiarios: Optional[list[str]] = None,
    dynamic_keywords: Optional[list[str]] = None,
    dynamic_org_codes: Optional[list[str]] = None,
    dynamic_suspicious_terms: Optional[list[str]] = None
) -> Dict[str, Any]:
    linha = _only_digits(raw_code)
    beneficiario_norm = _normalize_text(beneficiario)
    observacoes: list[str] = []

    dynamic_beneficiarios = dynamic_beneficiarios or []
    dynamic_keywords = dynamic_keywords or []
    dynamic_org_codes = dynamic_org_codes or []
    dynamic_suspicious_terms = dynamic_suspicious_terms or []

    if len(linha) not in {44, 47, 48}:
        return BoletoAnalysis(
            tipo="desconhecido",
            formato_entrada=f"{len(linha)}_digitos",
            linha_normalizada=linha,
            barcode_44="",
            valido_estrutura=False,
            valido_dv_campos=False,
            valido_dv_geral=False,
            banco_codigo=None,
            banco_nome="Desconhecido",
            categoria="desconhecido",
            risco="alto",
            score=95,
            mensagem="Quantidade de dígitos inválida para boleto bancário ou arrecadação.",
            valor=None,
            vencimento=None,
            observacoes=["Esperado: 44, 47 ou 48 dígitos."],
            segmento=None,
            segmento_descricao=None,
            empresa_orgao_codigo=None,
        ).__dict__

    # ========================================================
    # COBRANÇA BANCÁRIA
    # ========================================================
    if is_boleto_bancario_linha47(linha) or is_boleto_bancario_barcode44(linha):
        tipo = "cobranca_bancaria"
        formato_entrada = "linha47" if len(linha) == 47 else "barcode44"

        if len(linha) == 47:
            valido_campos = validar_campos_linha47(linha)
            barcode = linha47_to_barcode44(linha)
        else:
            valido_campos = True
            barcode = linha

        valido_geral = validar_dv_geral_barcode44_cobranca(barcode)
        banco_codigo = barcode[:3]
        categoria, banco_nome = get_categoria_por_codigo(banco_codigo)
        valor, vencimento = extrair_valor_e_vencimento_cobranca(barcode)

        score = 0

        if not valido_campos:
            score += 35
            observacoes.append("Falha nos DVs dos campos da linha digitável.")

        if not valido_geral:
            score += 45
            observacoes.append("Falha no DV geral do código de barras.")

        if categoria == "banco_tradicional":
            score += 5
            observacoes.append("Emissor associado a banco tradicional.")
        elif categoria == "cooperativa":
            score += 12
            observacoes.append("Emissor associado a cooperativa relevante.")
        elif categoria == "fintech_ou_digital":
            score += 25
            observacoes.append("Emissor associado a fintech/banco digital. Requer atenção extra.")
        elif categoria == "psp_ou_gateway":
            score += 30
            observacoes.append("Emissor associado a PSP/gateway. Validar beneficiário com atenção.")
        else:
            score += 45
            observacoes.append("Código de banco não reconhecido na base local.")

        if valor is not None and valor == 0:
            score += 8
            observacoes.append("Valor zerado. Pode ser legítimo em poucos casos, mas merece revisão.")

        if beneficiario_norm:
            if is_known_low_risk_beneficiary(beneficiario_norm, dynamic_beneficiarios):
                score = max(score - 10, 0)
                observacoes.append("Beneficiário compatível com entidade conhecida de baixo risco.")
            elif looks_government_like(beneficiario_norm, banco_codigo, tipo):
                score = max(score - 8, 0)
                observacoes.append("Beneficiário sugere ente governamental.")
            elif looks_concessionaria_like(beneficiario_norm, dynamic_keywords):
                score = max(score - 8, 0)
                observacoes.append("Beneficiário sugere concessionária/serviço essencial.")
            elif looks_suspicious_beneficiary(beneficiario_norm, dynamic_suspicious_terms):
                score += 20
                observacoes.append("Beneficiário contém termos incomuns ou suspeitos.")
        else:
            observacoes.append("Beneficiário não informado; análise ficou menos precisa.")

        risco = score_to_label(score)

        mensagem = {
            "baixo": "Baixo risco com base em estrutura, DVs e contexto do beneficiário. Ainda valide o recebedor final.",
            "medio": "Requer atenção. Estrutura pode estar válida, mas o contexto do emissor/beneficiário pede conferência adicional.",
            "alto": "Possível fraude ou documento inconsistente. Não pague sem validação manual do beneficiário.",
        }[risco]

        return BoletoAnalysis(
            tipo=tipo,
            formato_entrada=formato_entrada,
            linha_normalizada=linha,
            barcode_44=barcode,
            valido_estrutura=True,
            valido_dv_campos=valido_campos,
            valido_dv_geral=valido_geral,
            banco_codigo=banco_codigo,
            banco_nome=banco_nome,
            categoria=categoria,
            risco=risco,
            score=min(score, 100),
            mensagem=mensagem,
            valor=valor,
            vencimento=vencimento,
            observacoes=observacoes,
            segmento=None,
            segmento_descricao=None,
            empresa_orgao_codigo=None,
        ).__dict__

    # ========================================================
    # ARRECADAÇÃO / CONVÊNIOS / CONTAS
    # ========================================================
    if is_arrecadacao_linha48(linha) or is_arrecadacao_barcode44(linha):
        tipo = "arrecadacao"
        formato_entrada = "linha48" if len(linha) == 48 else "barcode44"

        if len(linha) == 48:
            valido_campos = validar_campos_linha48(linha)
            barcode = linha48_to_barcode44(linha)
        else:
            valido_campos = True
            barcode = linha

        valido_geral = validar_dv_geral_barcode44_arrecadacao(barcode)
        valor = extrair_valor_arrecadacao(barcode)

        segmento, segmento_descricao = extrair_segmento_arrecadacao(barcode)
        empresa_orgao_codigo = extrair_empresa_orgao_codigo(barcode)

        banco_codigo = None
        banco_nome = "Arrecadação / Convênio"
        categoria = "arrecadacao"

        score = 15

        if not valido_campos:
            score += 30
            observacoes.append("Falha nos DVs dos campos da linha de arrecadação.")

        if not valido_geral:
            score += 40
            observacoes.append("Falha no DV geral da arrecadação.")

        if segmento:
            observacoes.append(f"Segmento detectado: {segmento} - {segmento_descricao}.")
        else:
            score += 10
            observacoes.append("Segmento de arrecadação não identificado.")

        if empresa_orgao_codigo:
            observacoes.append(f"Código empresa/órgão extraído: {empresa_orgao_codigo}.")
            if empresa_orgao_parece_confiavel(empresa_orgao_codigo, dynamic_org_codes):
                score = max(score - 10, 0)
                observacoes.append("Código empresa/órgão compatível com base confiável local.")
            else:
                score += 5
                observacoes.append("Código empresa/órgão ainda não reconhecido na base local.")
        else:
            score += 8
            observacoes.append("Não foi possível extrair código empresa/órgão.")

        if beneficiario_norm:
            if looks_government_like(beneficiario_norm, None, tipo):
                score = max(score - 12, 0)
                observacoes.append("Beneficiário sugere arrecadação pública/governamental.")
            elif looks_concessionaria_like(beneficiario_norm, dynamic_keywords):
                score = max(score - 12, 0)
                observacoes.append("Beneficiário sugere concessionária ou serviço essencial.")
            elif is_known_low_risk_beneficiary(beneficiario_norm, dynamic_beneficiarios):
                score = max(score - 12, 0)
                observacoes.append("Beneficiário conhecido e compatível com arrecadação legítima.")
            elif looks_suspicious_beneficiary(beneficiario_norm, dynamic_suspicious_terms):
                score += 20
                observacoes.append("Beneficiário contém termos incomuns ou suspeitos.")
            else:
                score += 8
                observacoes.append("Arrecadação sem beneficiário claramente reconhecível.")
        else:
            score += 12
            observacoes.append("Beneficiário não informado em linha de arrecadação.")

        if segmento in {"2", "3", "4"}:
            score = max(score - 6, 0)
            observacoes.append("Segmento compatível com conta do dia a dia (saneamento, energia ou telecom).")

        if segmento in {"1", "5"}:
            score = max(score - 6, 0)
            observacoes.append("Segmento compatível com arrecadação pública/governamental.")

        if valor is not None and valor == 0:
            score += 5
            observacoes.append("Valor zerado em arrecadação. Requer conferência.")

        risco = score_to_label(score)

        mensagem = {
            "baixo": "Arrecadação com estrutura consistente e sinais compatíveis com conta ou guia legítima.",
            "medio": "Arrecadação estruturalmente válida, mas requer conferência do beneficiário, segmento e contexto.",
            "alto": "Arrecadação inconsistente ou sem indícios suficientes de legitimidade.",
        }[risco]

        return BoletoAnalysis(
            tipo=tipo,
            formato_entrada=formato_entrada,
            linha_normalizada=linha,
            barcode_44=barcode,
            valido_estrutura=True,
            valido_dv_campos=valido_campos,
            valido_dv_geral=valido_geral,
            banco_codigo=banco_codigo,
            banco_nome=banco_nome,
            categoria=categoria,
            risco=risco,
            score=min(score, 100),
            mensagem=mensagem,
            valor=valor,
            vencimento=None,
            observacoes=observacoes,
            segmento=segmento,
            segmento_descricao=segmento_descricao,
            empresa_orgao_codigo=empresa_orgao_codigo,
        ).__dict__

    # ========================================================
    # DESCONHECIDO
    # ========================================================
    return BoletoAnalysis(
        tipo="desconhecido",
        formato_entrada=f"{len(linha)}_digitos",
        linha_normalizada=linha,
        barcode_44="",
        valido_estrutura=False,
        valido_dv_campos=False,
        valido_dv_geral=False,
        banco_codigo=None,
        banco_nome="Desconhecido",
        categoria="desconhecido",
        risco="alto",
        score=90,
        mensagem="Formato numérico não reconhecido como cobrança bancária nem arrecadação.",
        valor=None,
        vencimento=None,
        observacoes=["Primeiro dígito/estrutura incompatível com os layouts suportados."],
        segmento=None,
        segmento_descricao=None,
        empresa_orgao_codigo=None,
    ).__dict__