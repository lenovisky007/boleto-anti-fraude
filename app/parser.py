from app.utils.helpers import only_digits


def extract_basic_info(raw_code: str):
    code = only_digits(raw_code)

    return {
        "raw": raw_code,
        "digits": code,
        "length": len(code),
        "type": detect_type(code)
    }


def detect_type(code: str) -> str:
    if len(code) == 47:
        return "boleto_bancario_linha_digitavel"
    if len(code) == 48:
        return "arrecadacao_convenio"
    if len(code) == 44:
        return "codigo_barras"
    return "desconhecido"