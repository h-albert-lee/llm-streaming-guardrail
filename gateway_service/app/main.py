from fastapi import FastAPI
from app.routes import router

def create_app():
    app = FastAPI(title="Gateway Service - LLM Streaming with Safety Check")
    app.include_router(router)
    return app

app = create_app()
