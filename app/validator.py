from app.parser import extract_basic_info


def validate_boleto(raw_code: str):
    info = extract_basic_info(raw_code)

    errors = []
    valid = True

    if info["type"] == "desconhecido":
        valid = False
        errors.append("Formato inválido")

    if info["length"] not in [44, 47, 48]:
        valid = False
        errors.append("Tamanho inválido")

    return {
        "valid": valid,
        "info": info,
        "errors": errors
    }