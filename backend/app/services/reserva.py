from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import MovimentoReserva


def totais(db: Session) -> tuple[float, float]:
    linhas = dict(
        db.query(MovimentoReserva.tipo, func.sum(MovimentoReserva.valor))
        .group_by(MovimentoReserva.tipo)
        .all()
    )
    return round(float(linhas.get("aporte") or 0), 2), round(float(linhas.get("saque") or 0), 2)


def primeira_data_negativa(movimentos: list[MovimentoReserva]):
    acumulado = 0.0
    ordem = sorted(movimentos, key=lambda m: (m.data, m.tipo != "aporte", m.id or 0))
    for m in ordem:
        acumulado += m.valor if m.tipo == "aporte" else -m.valor
        if acumulado < -0.005:
            return m.data
    return None


def saldo(db: Session) -> float:
    aportes, saques = totais(db)
    return round(aportes - saques, 2)
