from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from ..models import Transacao
from .fatura import gasto_cartao_por_categoria
from .recorrentes import previsoes_do_mes


def por_categoria(db: Session, mes: int, ano: int, tipo: str = "despesa") -> dict[str, float]:
    linhas = (
        db.query(Transacao.categoria, func.sum(Transacao.valor))
        .filter(
            Transacao.tipo == tipo,
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano,
        )
        .group_by(Transacao.categoria)
        .all()
    )
    totais = {categoria: round(float(total), 2) for categoria, total in linhas}
    for p in previsoes_do_mes(db, mes, ano):
        if p.molde.tipo == tipo:
            c = p.molde.categoria
            totais[c] = round(totais.get(c, 0.0) + p.molde.valor, 2)
    if tipo == "despesa":
        for categoria, valor in gasto_cartao_por_categoria(db, mes, ano).items():
            totais[categoria] = round(totais.get(categoria, 0.0) + valor, 2)
    return totais
