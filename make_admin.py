from database import SessionLocal
from models import User

db = SessionLocal()

email = input("Digite o email do usuário: ")

user = db.query(User).filter(User.email == email).first()

if not user:
    print("Usuário não encontrado")
else:
    user.is_admin = True
    db.commit()
    print("Usuário agora é ADMIN")