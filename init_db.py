from app.database.db import Base, engine
from app.models import User  # garante que o model seja carregado

print("Criando tabelas no banco...")

Base.metadata.create_all(bind=engine)

print("Banco inicializado com sucesso!")