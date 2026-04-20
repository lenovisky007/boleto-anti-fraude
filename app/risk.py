from app.validator import validate_boleto


def calculate_risk(raw_code: str, beneficiario: str = None):
    result = validate_boleto(raw_code)

    score = 0
    alerts = []

    # ❌ invalido = risco alto direto
    if not result["valid"]:
        return {
            "score": 95,
            "risk": "alto",
            "alerts": result["errors"],
            "data": result
        }

    info = result["info"]

    # 📊 regra 1: tipo desconhecido
    if info["type"] == "desconhecido":
        score += 40
        alerts.append("Tipo de boleto desconhecido")

    # 📊 regra 2: tamanho suspeito
    if info["length"] not in [44, 47, 48]:
        score += 50
        alerts.append("Estrutura fora do padrão")

    # 📊 regra 3: beneficiário suspeito (básico)
    if beneficiario:
        b = beneficiario.lower()

        if any(x in b for x in ["teste", "fake", "intermediador"]):
            score += 30
            alerts.append("Beneficiário suspeito")

    # 📊 regra final
    if score <= 30:
        risk = "baixo"
    elif score <= 70:
        risk = "medio"
    else:
        risk = "alto"

    return {
        "score": min(score, 100),
        "risk": risk,
        "alerts": alerts,
        "parsed": info
    }