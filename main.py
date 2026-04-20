from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from auth import register_user, login_user, get_current_user
from models import User

app = FastAPI()

# cria o banco automaticamente
Base.metadata.create_all(bind=engine)


# =========================
# DEPENDÊNCIA DO BANCO
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# ROTAS
# =========================

@app.post("/register")
def register(data: dict, db: Session = Depends(get_db)):
    return register_user(data["username"], data["password"], db)


@app.post("/login")
def login(data: dict, db: Session = Depends(get_db)):
    return login_user(data["username"], data["password"], db)


@app.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return {
        "username": user.username,
        "plan": user.plan,
        "is_admin": user.is_admin
    }