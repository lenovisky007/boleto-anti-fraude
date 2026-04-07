from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()
@app.post("/register")
def register(...):

@app.post("/login")
def login(...):

@app.get("/me")
def me(...):

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def limpar_linha(linha: str) -> str:
    return re.sub(r"\D", "", linha)

def identificar_banco(linha: str) -> str:
    bancos = {
        "001": "Banco do Brasil",
        "104": "Caixa",
        "237": "Bradesco",
        "341": "Itaú",
    }
    return bancos.get(linha[:3], "Desconhecido")

@app.get("/")
def home():
    return {"status": "API rodando 🚀"}

@app.post("/analisar")
def analisar(payload: dict):
    linha_digitavel = payload.get("linha_digitavel", "")
    linha = limpar_linha(linha_digitavel)
    banco = identificar_banco(linha)

    return {
        "banco": banco,
        "linha": linha
    }
import os

API_KEY = os.getenv("API_KEY")
from fastapi import Header, HTTPException

@app.post("/analisar")
def analisar(payload: dict, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")

    linha_digitavel = payload.get("linha_digitavel", "")
    linha = limpar_linha(linha_digitavel)
    banco = identificar_banco(linha)

    return {
        "banco": banco,
        "linha": linha
    }