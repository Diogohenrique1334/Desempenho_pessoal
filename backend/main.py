import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from app.models.database import Base, engine
from app.whatsapp.handlers import verificar_webhook, processar_webhook

app = FastAPI(title="Habit Tracker API")


@app.on_event("startup")
def criar_tabelas():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "online"}


@app.get("/webhook")
def webhook_verify(request: Request):
    return verificar_webhook(request)


@app.post("/webhook")
async def webhook_post(request: Request):
    return await processar_webhook(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
