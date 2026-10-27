from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ORIGENS_CORS
from .database import inicializar_banco
from .routers import (
    cartoes,
    dashboard,
    dividas,
    mes,
    opcoes,
    orcamento,
    projecao,
    reserva,
    sistema,
    transacoes,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    inicializar_banco()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Painel Financeiro",
    description="API pessoal de finanças — transações, cartões, dívidas, reserva e orçamento.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_CORS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transacoes.router)
app.include_router(cartoes.router)
app.include_router(dividas.router)
app.include_router(reserva.router)
app.include_router(orcamento.router)
app.include_router(dashboard.router)
app.include_router(projecao.router)
app.include_router(mes.router)
app.include_router(opcoes.router)
app.include_router(sistema.router)


@app.get("/")
def raiz():
    return {"app": "Painel Financeiro", "docs": "/docs"}
