from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from ..models import Divida, Transacao


def _quitacoes_concluidas(db: Session) -> Query:
    return db.query(Transacao).filter(
        Transacao.tipo == "quitacao",
        Transacao.situacao == "concluido",
        Transacao.divida_id.isnot(None),
    )


def pago_vinculado(db: Session, divida_id: int, ignorar_id: int | None = None) -> float:
    query = _quitacoes_concluidas(db).filter(Transacao.divida_id == divida_id)
    if ignorar_id is not None:
        query = query.filter(Transacao.id != ignorar_id)
    with db.no_autoflush:
        total = query.with_entities(func.coalesce(func.sum(Transacao.valor), 0)).scalar()
    return round(float(total), 2)


def pagos_vinculados(db: Session) -> dict[int, float]:
    linhas = (
        _quitacoes_concluidas(db)
        .with_entities(Transacao.divida_id, func.sum(Transacao.valor))
        .group_by(Transacao.divida_id)
        .all()
    )
    return {divida_id: round(float(total), 2) for divida_id, total in linhas}


def restante(divida: Divida, vinculado: float) -> float:
    return round(max(divida.valor_inicial - (divida.total_pago + vinculado), 0.0), 2)


def total_restante(db: Session) -> float:
    vinculados = pagos_vinculados(db)
    abertas = db.query(Divida).filter(Divida.status != "concluido").all()
    return round(sum(restante(d, vinculados.get(d.id, 0.0)) for d in abertas), 2)


def recalcular_status(db: Session, divida_id: int | None) -> None:
    if divida_id is None:
        return
    divida = db.get(Divida, divida_id)
    if not divida or divida.valor_inicial <= 0:
        return
    quitada = divida.total_pago + pago_vinculado(db, divida.id) >= divida.valor_inicial
    if quitada and divida.status != "concluido":
        divida.status = "concluido"
    elif not quitada and divida.status == "concluido":
        divida.status = "em_andamento"
    else:
        return
    db.commit()
