from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def limpar_linha(linha):
    return re.sub(r'\D', '', linha)

def identificar_banco(linha):
    bancos = {
        "001": "Banco do Brasil",
        "237": "Bradesco",
        "341": "Itaú",
        "104": "Caixa"
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