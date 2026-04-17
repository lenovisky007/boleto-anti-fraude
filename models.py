from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# =========================
# USUÁRIOS
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    plan = Column(String, default="free")
    monthly_limit = Column(Integer, default=10)

    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# CONTROLE DE USO
# =========================
class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


# =========================
# ENTIDADES DINÂMICAS (PAINEL ADMIN)
# =========================
class TrustedEntity(Base):
    __tablename__ = "trusted_entities"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    # tipos possíveis:
    # beneficiario
    # keyword
    # org_code
    # suspicious_term

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# RESULTADO COMPLETO DAS ANÁLISES (RELATÓRIOS PDF)
# =========================
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # origem da análise
    source_type = Column(String, nullable=False)  # manual ou pdf
    source_file_name = Column(String, nullable=True)
    extraction_method = Column(String, nullable=True)

    # dados do boleto
    linha_digitavel = Column(String, nullable=False)
    beneficiario = Column(String, nullable=True)

    tipo = Column(String, nullable=True)
    banco_nome = Column(String, nullable=True)
    categoria = Column(String, nullable=True)

    risco = Column(String, nullable=True)
    score = Column(Integer, nullable=True)

    valor = Column(String, nullable=True)
    vencimento = Column(String, nullable=True)

    segmento = Column(String, nullable=True)
    segmento_descricao = Column(String, nullable=True)
    empresa_orgao_codigo = Column(String, nullable=True)

    # validações
    valido_dv_campos = Column(Boolean, default=False)
    valido_dv_geral = Column(Boolean, default=False)

    # observações do motor antifraude
    observacoes = Column(Text, nullable=True)

    # timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")