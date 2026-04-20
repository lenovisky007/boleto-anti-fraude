from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from models import User
import uuid

def get_current_user(request: Request, db: Session):
    token = request.headers.get("Authorization")

    if not token:
        raise HTTPException(status_code=401, detail="Token não enviado")

    user = db.query(User).filter(User.token == token).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário inválido")

    return user


def register_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()

    if user:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    token = str(uuid.uuid4())

    new_user = User(
        username=username,
        password=password,
        token=token
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(username: str, password: str, db: Session):
    user = db.query(User).filter(
        User.username == username,
        User.password == password
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Login inválido")

    return user


def require_admin(user):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado")