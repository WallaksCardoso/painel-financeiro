import os
from datetime import date, datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import inspect as sa_inspect

from ..config import CAMINHO_DB
from ..database import Db
from ..models import (
    Cartao,
    CompraCartao,
    Configuracao,
    Divida,
    FaturaPaga,
    MovimentoReserva,
    Opcao,
    OrcamentoCategoria,
    PlanoMes,
    Transacao,
)

router = APIRouter(prefix="/api", tags=["sistema"])

_MODELOS = {
    "transacoes": Transacao,
    "dividas": Divida,
    "movimentos_reserva": MovimentoReserva,
    "orcamento_categorias": OrcamentoCategoria,
    "cartoes": Cartao,
    "compras_cartao": CompraCartao,
    "faturas_pagas": FaturaPaga,
    "opcoes": Opcao,
    "configuracoes": Configuracao,
    "planos_mes": PlanoMes,
}


def _serializavel(valor):
    if isinstance(valor, datetime | date):
        return valor.isoformat()
    return valor


def _linha_para_dict(obj) -> dict:
    colunas = sa_inspect(obj).mapper.column_attrs.keys()
    return {c: _serializavel(getattr(obj, c)) for c in colunas}


@router.get("/exportar")
def exportar(db: Db):
    dados = {
        nome: [_linha_para_dict(o) for o in db.query(modelo).all()]
        for nome, modelo in _MODELOS.items()
    }
    dados["_exportado_em"] = datetime.now().isoformat()
    nome_arquivo = f"painel-financeiro-{date.today().isoformat()}.json"
    return JSONResponse(
        content=dados,
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


@router.get("/backup")
def backup():
    if not os.path.exists(CAMINHO_DB):
        raise HTTPException(status_code=404, detail="Banco não encontrado")
    return FileResponse(
        CAMINHO_DB,
        media_type="application/octet-stream",
        filename=f"painel-{date.today().isoformat()}.db",
    )
