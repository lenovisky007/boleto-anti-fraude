from database import SessionLocal
from models import TrustedEntity

def load_dynamic_entities():
    db = SessionLocal()
    try:
        entities = db.query(TrustedEntity).all()

        beneficiarios = []
        keywords = []
        org_codes = []
        suspicious_terms = []

        for e in entities:
            if e.type == "beneficiario":
                beneficiarios.append(e.name)
            elif e.type == "keyword":
                keywords.append(e.name)
            elif e.type == "org_code":
                org_codes.append(e.name)
            elif e.type == "suspicious_term":
                suspicious_terms.append(e.name)

        return {
            "beneficiarios": beneficiarios,
            "keywords": keywords,
            "org_codes": org_codes,
            "suspicious_terms": suspicious_terms
        }
    finally:
        db.close()