import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from app.models.database import Base, engine
from app.whatsapp.handlers import verificar_webhook, processar_webhook

app = FastAPI(title="Habit Tracker API")


@app.on_event("startup")
def criar_tabelas():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "online"}


@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    return """
    <html>
    <head><title>Política de Privacidade — Habit Tracker</title></head>
    <body style="font-family: sans-serif; max-width: 700px; margin: 40px auto; line-height: 1.6;">
        <h1>Política de Privacidade</h1>
        <p>Este aplicativo (Habit Tracker) coleta e armazena os seguintes dados para fornecer
        o serviço de rastreamento de hábitos pessoais via WhatsApp:</p>
        <ul>
            <li>Número de telefone do WhatsApp, usado como identificador do usuário</li>
            <li>Nome informado pelo usuário durante o cadastro</li>
            <li>Hábitos configurados pelo usuário e seus registros diários (sim/não, notas, horários)</li>
        </ul>
        <p>Esses dados são armazenados em banco de dados (PostgreSQL) e usados exclusivamente
        para gerar o dashboard de acompanhamento pessoal do próprio usuário. Não compartilhamos
        dados com terceiros.</p>
        <p>O usuário pode solicitar a exclusão de seus dados a qualquer momento entrando em
        contato pelo e-mail: diogohenrique1334@gmail.com</p>
    </body>
    </html>
    """


@app.get("/webhook")
def webhook_verify(request: Request):
    return verificar_webhook(request)


@app.post("/webhook")
async def webhook_post(request: Request):
    return await processar_webhook(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
