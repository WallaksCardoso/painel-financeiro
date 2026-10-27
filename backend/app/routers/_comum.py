from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..database import Base

M = TypeVar("M", bound=Base)


def obter_ou_404(db: Session, modelo: type[M], id_: int, mensagem: str) -> M:
    obj = db.get(modelo, id_)
    if obj is None:
        raise HTTPException(status_code=404, detail=mensagem)
    return obj


NOME_DO_GRUPO = {
    "categoria": ("Categoria", "a"),
    "meio_pagamento": ("Meio de pagamento", "o"),
    "origem_reserva": ("Origem", "a"),
}


def formatar_real(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_numero(valor: float) -> str:
    if float(valor).is_integer():
        return f"{int(valor):,}".replace(",", ".")
    return f"{valor:g}".replace(".", ",")


def validar_opcao(db: Session, grupo: str, chave: str | None) -> None:
    from ..models import Opcao

    if chave is None:
        return
    existe = db.query(Opcao).filter(Opcao.grupo == grupo, Opcao.chave == chave).first()
    if existe is None:
        nome, g = NOME_DO_GRUPO[grupo]
        raise HTTPException(
            status_code=422,
            detail=f'{nome} "{chave}" não está cadastrad{g}. '
            f"Cadastre em Configurações ou escolha outr{g}.",
        )
