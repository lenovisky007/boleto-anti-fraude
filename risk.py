from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Dict, Any


# ============================================================
# BASES DE INSTITUIÇÕES
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
    "263": "Banco Cacique",
    "265": "Banco Fator",
    "266": "Banco Cédula",
    "300": "Banco de La Nacion Argentina",
    "318": "Banco BMG",
    "320": "Banco Industrial do Brasil",
    "323": "Mercado Pago",
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

# Heurísticas para arrecadação pública:
# Para governo, banco sozinho não basta. Beneficiário/descrição ajudam.
GOV_BANK_HINTS = {"001", "104"}
GOV_BENEFICIARY_KEYWORDS = [
    "receita federal",
    "tesouro nacional",
    "prefeitura",
    "secretaria da fazenda",
    "estado de",
    "municipio de",
    "muncipio de",  # tolerância a erro comum
    "detran",
    "tribunal",
    "inss",
    "fgts",
    "gru",
    "simples nacional",
    "sefaz",
    "fazenda",
    "autarquia",
]


# ============================================================
# ESTRUTURAS
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


# ============================================================
# FUNÇÕES BÁSICAS
# ============================================================

def _only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


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
    """
    DV geral de boleto bancário.
    Se der 0, 10 ou 11, retorna 1.
    """
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
    """
    Uma forma usada em arrecadação/convênios.
    """
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
    """
    Base clássica FEBRABAN: 1997-10-07.
    Alguns contextos mais novos usam revisões do fator.
    Se o fator não for plausível, retorna None.
    """
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
# BOLETO BANCÁRIO (44 / 47)
# ============================================================

def is_boleto_bancario_barcode44(code: str) -> bool:
    return len(code) == 44 and code[:3].isdigit() and code[3] == "9"


def is_boleto_bancario_linha47(code: str) -> bool:
    return len(code) == 47 and code[:3].isdigit() and code[3] == "9"


def linha47_to_barcode44(linha: str) -> str:
    """
    Converte linha digitável de cobrança (47) em código de barras (44).
    Campos:
      1: 1-9
      2: 10-20
      3: 21-31
      4: 32
      5: 33-47
    """
    # linha sem pontuação
    campo1 = linha[0:9]
    campo2 = linha[10:20]
    campo3 = linha[21:31]
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
# ARRECADAÇÃO / CONVÊNIOS (44 / 48)
# ============================================================

def is_arrecadacao_barcode44(code: str) -> bool:
    return len(code) == 44 and code[0] == "8"


def is_arrecadacao_linha48(code: str) -> bool:
    return len(code) == 48 and code[0] == "8"


def linha48_to_barcode44(linha: str) -> str:
    """
    Arrecadação em 4 blocos de 12:
      cada bloco = 11 dados + 1 DV
    remove DVs de bloco e concatena
    """
    blocos = [linha[i:i+12] for i in range(0, 48, 12)]
    dados = [b[:11] for b in blocos]
    return "".join(dados)


def arrecadacao_usa_modulo10(barcode44: str) -> bool:
    """
    Na arrecadação, a posição 3 (índice 2) define o tipo de DV/valor.
    Valores 6 ou 7 => módulo 10
    Valores 8 ou 9 => módulo 11
    """
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
    """
    Na arrecadação, o segmento e o valor efetivo variam pela modalidade.
    Em muitos casos, posições 4-14 representam valor.
    """
    valor_ref = barcode[2]
    valor_str = barcode[4:15]

    if valor_ref in {"6", "8"} and valor_str.isdigit():
        return int(valor_str) / 100

    if valor_ref in {"7", "9"} and valor_str.isdigit():
        return int(valor_str) / 100

    return None


# ============================================================
# CLASSIFICAÇÃO DE INSTITUIÇÃO
# ============================================================

def get_categoria_por_codigo(codigo: Optional[str]) -> tuple[str, str]:
    if not codigo:
        return "desconhecido", "Desconhecido"

    if codigo in BANCOS_TRADICIONAIS and codigo not in FINTECHS_E_DIGITAIS:
        return "banco_tradicional", BANCOS_TRADICIONAIS[codigo]

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
    beneficiario_norm = (beneficiario or "").strip().lower()

    if tipo == "arrecadacao" and any(k in beneficiario_norm for k in GOV_BENEFICIARY_KEYWORDS):
        return True

    if banco_codigo in GOV_BANK_HINTS and any(k in beneficiario_norm for k in GOV_BENEFICIARY_KEYWORDS):
        return True

    return False


# ============================================================
# MOTOR DE RISCO
# ============================================================

def score_to_label(score: int) -> str:
    if score <= 25:
        return "baixo"
    if score <= 55:
        return "medio"
    return "alto"


def analyze_boleto(raw_code: str, beneficiario: Optional[str] = None) -> Dict[str, Any]:
    linha = _only_digits(raw_code)
    observacoes: list[str] = []

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
        ).__dict__

    # --------------------------------------------------------
    # COBRANÇA BANCÁRIA
    # --------------------------------------------------------
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
            score += 15
            observacoes.append("Emissor associado a cooperativa relevante.")
        elif categoria == "fintech_ou_digital":
            score += 30
            observacoes.append("Emissor associado a fintech/banco digital. Requer atenção extra.")
        elif categoria == "psp_ou_gateway":
            score += 35
            observacoes.append("Emissor associado a PSP/gateway. Validar beneficiário com atenção.")
        else:
            score += 50
            observacoes.append("Código de banco não reconhecido na base local.")

        if valor is not None and valor == 0:
            score += 10
            observacoes.append("Valor zerado. Pode ser legítimo em poucos casos, mas merece revisão.")

        if beneficiario:
            if looks_government_like(beneficiario, banco_codigo, tipo):
                score = max(score - 10, 0)
                observacoes.append("Beneficiário sugere arrecadação pública/ente governamental.")
        else:
            observacoes.append("Beneficiário não informado; análise ficou menos precisa.")

        risco = score_to_label(score)

        mensagem = {
            "baixo": "Baixo risco com base em estrutura, DVs e categoria do emissor. Ainda valide o beneficiário.",
            "medio": "Requer atenção. Estrutura pode estar válida, mas o emissor/cenário pede conferência adicional.",
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
        ).__dict__

    # --------------------------------------------------------
    # ARRECADAÇÃO / CONVÊNIOS
    # --------------------------------------------------------
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
        banco_codigo = None  # arrecadação não usa a mesma semântica do código bancário
        banco_nome = "Arrecadação / Convênio"
        categoria = "arrecadacao"

        score = 10

        if not valido_campos:
            score += 35
            observacoes.append("Falha nos DVs dos campos da linha de arrecadação.")

        if not valido_geral:
            score += 45
            observacoes.append("Falha no DV geral da arrecadação.")

        if beneficiario:
            if looks_government_like(beneficiario, None, tipo):
                score = max(score - 10, 0)
                observacoes.append("Beneficiário sugere arrecadação governamental/publicada.")
            else:
                score += 15
                observacoes.append("Arrecadação sem beneficiário governamental reconhecível.")
        else:
            score += 20
            observacoes.append("Beneficiário não informado em linha de arrecadação.")

        risco = score_to_label(score)

        mensagem = {
            "baixo": "Arrecadação com estrutura consistente e indícios de beneficiário legítimo.",
            "medio": "Arrecadação válida estruturalmente, mas requer atenção ao beneficiário e ao contexto.",
            "alto": "Arrecadação inconsistente ou com sinais insuficientes de legitimidade.",
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
        ).__dict__

    # --------------------------------------------------------
    # NENHUM FORMATO RECONHECIDO
    # --------------------------------------------------------
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
    ).__dict__