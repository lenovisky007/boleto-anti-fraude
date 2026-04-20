from fastapi import FastAPI

def create_app():
    app = FastAPI(
        title="Boleto Antifraude",
        version="1.0.0",
        docs_url="/docs"
    )

    # Aqui você vai registrar rotas depois
    # from .routes.boleto_routes import router
    # app.include_router(router)

    return app