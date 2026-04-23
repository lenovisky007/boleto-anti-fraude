from app.database import Base, engine
from app.models import User

print("Criando tabelas no banco...")

Base.metadata.create_all(bind=engine)

print("Banco inicializado com sucesso!")