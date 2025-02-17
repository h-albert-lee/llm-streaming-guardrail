from fastapi import FastAPI
from app.routes import router

def create_app():
    app = FastAPI(title="Safety Service with LLaMA Guard - Batch Inference")
    app.include_router(router)
    return app

app = create_app()
