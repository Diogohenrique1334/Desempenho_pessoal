# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este projeto

SaaS de rastreamento de hábitos pessoais multi-usuário. Cada usuário configura seus próprios hábitos via WhatsApp (onboarding conversacional) e analisa seus dados em um dashboard Streamlit com autenticação Google.

Projeto irmão: existe um rastreador pessoal (Diogo + Michele) em produção no Render, em outra pasta. Este aqui é a versão escalável e multi-tenant, construída do zero com schema dinâmico.

## Stack

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL Neon
- **Frontend**: Streamlit com `st.login()` (Google OAuth) + ECharts via `streamlit-echarts`
- **Mensageria**: WhatsApp Cloud API (Meta) via webhooks
- **Deploy**: Render (serviços separados para backend e frontend)

## Comandos

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && streamlit run main.py

# Migrations (Alembic)
cd backend && alembic upgrade head
alembic revision --autogenerate -m "descricao"
```

## Arquitetura

### Schema do banco (dinâmico por usuário)

```
usuarios        → phone, nome, email (para vincular ao login Google)
habitos_config  → usuario_id, nome, tipo (bool/nota/hora), ordem, ativo
registros       → usuario_id, data  [UNIQUE(usuario_id, data)], status_conversa
registros_valor → registro_id, habito_id, valor (TEXT)
```

`valor` é sempre TEXT e parseado conforme o `tipo` do hábito. UNIQUE(registro_id, habito_id) garante idempotência.

### Backend — camadas

```
backend/
├── main.py                      # FastAPI app + routers
└── app/
    ├── models/                  # SQLAlchemy models + Pydantic schemas + session
    ├── whatsapp/
    │   ├── client.py            # Wrapper WhatsApp Cloud API (texto, botões, listas)
    │   └── handlers.py          # Roteador de webhooks
    ├── conversation/
    │   ├── engine.py            # Dispatcher: onboarding vs. registro diário
    │   ├── onboarding.py        # Fluxo novo usuário: nome → seleção de hábitos
    │   └── registro.py          # Fluxo diário: toggle hábitos, entrada de métricas
    ├── services/                # Lógica de negócio isolada (sem dependência de HTTP)
    └── utils.py                 # FUSO_BRASIL, agora_brasil(), data_hoje_brasil()
```

### Frontend — camadas

```
frontend/
├── main.py                      # Entry point Streamlit + st.login()
├── auth.py                      # Mapeia email Google → usuario_id no banco
└── pages/
    ├── dashboard.py             # Visão geral de aderência
    ├── analise.py               # Análise causal, Granger, clustering (fase 2)
    └── configuracoes.py         # Gerenciar hábitos do usuário
```

### Fluxo de conversação (WhatsApp)

O estado da conversa fica no campo `status_conversa` da tabela `registros` (e `onboarding_step` em `usuarios`). O dispatcher em `conversation/engine.py` decide qual fluxo acionar com base nesses campos:

- **Novo usuário** (`onboarding_step != null`) → `onboarding.py`
- **Usuário ativo, sem status** → exibe menu principal (Hoje/Ontem → Hábitos/Métricas)
- **Usuário ativo, com status** → `registro.py` processa texto de entrada (nota/hora)

Hábitos do tipo `bool` são toggleados diretamente no clique (sem aguardar texto). Hábitos do tipo `nota` e `hora` usam `status_conversa` para aguardar a resposta de texto do usuário.

### Autenticação no frontend

`st.login()` retorna o email Google do usuário. `auth.py` faz lookup em `usuarios.email` e retorna o `usuario_id`. Sem match → página de instruções para entrar em contato (não há auto-cadastro pelo frontend).

## Decisões de design a preservar

- **valor TEXT genérico**: não criar colunas por hábito. Toda query de análise faz cast do TEXT para o tipo correto.
- **Idempotência no webhook**: antes de processar, checar `message_id` para evitar reprocessamento (WhatsApp re-envia webhooks).
- **Separação serviços/handlers**: funções em `services/` não recebem `Request` do FastAPI — são testáveis sem subir o servidor.
