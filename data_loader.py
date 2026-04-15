import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

KNOWN_LOW_RISK_BENEFICIARIES = load_json("beneficiarios_confiaveis.json")
CONCESSIONARIA_KEYWORDS = load_json("keywords_concessionarias.json")
GOV_BENEFICIARY_KEYWORDS = load_json("gov_keywords.json")
KNOWN_PUBLIC_OR_SERVICE_CODES = load_json("orgaos_codigos.json")