from fastapi import FastAPI
from .routes.boleto_routes import router as boleto_router

app = FastAPI(title="Boleto Antifraude")

@app.get("/")
def home():
    return {"status": "API rodando 🚀"}

app.include_router(boleto_router)