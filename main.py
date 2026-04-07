from fastapi import FastAPI
import re

app = FastAPI()

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
def analisar(linha_digitavel: str):
    linha = limpar_linha(linha_digitavel)
    
    banco = identificar_banco(linha)
    
    return {
        "banco": banco,
        "linha": linha
    }