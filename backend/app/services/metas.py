import calendar
import math
from dataclasses import dataclass
from datetime import date

from sqlalchemy import extract
from sqlalchemy.orm import Session

from ..models import MetaPoupanca, MovimentoReserva, PlanoMes


@dataclass
class Meta:
    valor: float | None
    origem: str | None
    orcamento_variavel: float | None


def _indice(mes: int, ano: int) -> int:
    return ano * 12 + mes


def meta_vigente(db: Session, mes: int, ano: int) -> MetaPoupanca | None:
    alvo = _indice(mes, ano)
    metas = [m for m in db.query(MetaPoupanca).all() if _indice(m.mes, m.ano) <= alvo]
    return max(metas, key=lambda m: _indice(m.mes, m.ano), default=None)


def meta_do_mes(db: Session, mes: int, ano: int) -> Meta:
    vigente = meta_vigente(db, mes, ano)
    orcamento = vigente.orcamento_variavel if vigente else None
    plano = db.query(PlanoMes).filter(PlanoMes.mes == mes, PlanoMes.ano == ano).first()
    if plano is not None and plano.meta_valor is not None:
        return Meta(round(plano.meta_valor, 2), "mes", orcamento)
    if vigente is not None:
        return Meta(round(vigente.valor, 2), "recorrente", orcamento)
    return Meta(None, None, None)


def reserva_liquida_no_mes(db: Session, mes: int, ano: int) -> float:
    movimentos = (
        db.query(MovimentoReserva)
        .filter(
            extract("month", MovimentoReserva.data) == mes,
            extract("year", MovimentoReserva.data) == ano,
        )
        .all()
    )
    total = sum(m.valor if m.tipo == "aporte" else -m.valor for m in movimentos)
    return round(total, 2)


def semanas_restantes(mes: int, ano: int, hoje: date) -> int:
    if (ano, mes) < (hoje.year, hoje.month):
        return 0
    dias_no_mes = calendar.monthrange(ano, mes)[1]
    if (ano, mes) == (hoje.year, hoje.month):
        return math.ceil((dias_no_mes - hoje.day + 1) / 7)
    return math.ceil(dias_no_mes / 7)
