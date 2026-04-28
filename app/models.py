from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


# ============================================================
# USUÁRIOS
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    plan = Column(String(50), default="free")
    monthly_limit = Column(Integer, default=10)

    is_admin = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # relacionamento
    analyses = relationship("AnalysisResult", back_populates="user", cascade="all, delete")
    logs = relationship("AnalysisLog", back_populates="user", cascade="all, delete")


# ============================================================
# LOG DE USO (CONTROLE DE LIMITE)
# ============================================================

class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="logs")


# ============================================================
# ENTIDADES DINÂMICAS (ADMIN)
# ============================================================

class TrustedEntity(Base):
    __tablename__ = "trusted_entities"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(180), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    # tipos:
    # beneficiario
    # keyword
    # org_code
    # suspicious_term

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class TrustedEntity(Base):
    __tablename__ = "trusted_entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# RESULTADOS DAS ANÁLISES
# ============================================================

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # origem
    source_type = Column(String(20), nullable=False)  # manual | pdf
    source_file_name = Column(String(255), nullable=True)
    extraction_method = Column(String(50), nullable=True)

    # dados principais
    linha_digitavel = Column(String(60), nullable=False, index=True)
    beneficiario = Column(String(255), nullable=True, index=True)

    tipo = Column(String(50), nullable=True)
    banco_nome = Column(String(120), nullable=True)
    categoria = Column(String(50), nullable=True)

    risco = Column(String(20), nullable=True, index=True)
    score = Column(Integer, nullable=True)

    valor = Column(String(50), nullable=True)
    vencimento = Column(String(20), nullable=True)

    segmento = Column(String(10), nullable=True)
    segmento_descricao = Column(String(120), nullable=True)
    empresa_orgao_codigo = Column(String(20), nullable=True)

    # validações
    valido_dv_campos = Column(Boolean, default=False)
    valido_dv_geral = Column(Boolean, default=False)

    # antifraude
    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # relacionamento
    user = relationship("User", back_populates="analyses")