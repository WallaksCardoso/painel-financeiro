from fastapi import APIRouter, HTTPException

from ..database import Db
from ..models import MovimentoReserva
from ..schemas import (
    MovimentoReservaCreate,
    MovimentoReservaOut,
    MovimentoReservaUpdate,
    ReservaSaldo,
)
from ..services import reserva as svc
from ._comum import obter_ou_404, validar_opcao

router = APIRouter(prefix="/api/reserva", tags=["reserva"])


@router.get("", response_model=list[MovimentoReservaOut])
def listar(db: Db):
    return (
        db.query(MovimentoReserva)
        .order_by(MovimentoReserva.data.desc(), MovimentoReserva.id.desc())
        .all()
    )


@router.get("/saldo", response_model=ReservaSaldo)
def saldo(db: Db):
    aportes, saques = svc.totais(db)
    return ReservaSaldo(
        saldo=round(aportes - saques, 2),
        total_aportes=aportes,
        total_saques=saques,
        quantidade_movimentos=db.query(MovimentoReserva).count(),
    )


@router.post("", response_model=MovimentoReservaOut, status_code=201)
def criar(db: Db, payload: MovimentoReservaCreate):
    validar_opcao(db, "origem_reserva", payload.origem)
    movimento = MovimentoReserva(**payload.model_dump())
    if payload.tipo == "saque":
        if payload.valor > svc.saldo(db):
            raise HTTPException(
                status_code=400,
                detail="Saque maior que o saldo disponível na reserva.",
            )
        existentes = db.query(MovimentoReserva).all()
        negativa = svc.primeira_data_negativa([*existentes, movimento])
        if negativa:
            raise HTTPException(
                status_code=400,
                detail="Nessa data ainda não havia saldo suficiente: a reserva ficaria "
                f"negativa em {negativa:%d/%m/%Y}.",
            )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    return movimento


@router.patch("/{movimento_id}", response_model=MovimentoReservaOut)
def atualizar(db: Db, movimento_id: int, payload: MovimentoReservaUpdate):
    movimento = obter_ou_404(db, MovimentoReserva, movimento_id, "Movimento não encontrado")
    dados = payload.model_dump(exclude_unset=True)
    validar_opcao(db, "origem_reserva", dados.get("origem"))
    for campo, valor in dados.items():
        setattr(movimento, campo, valor)
    with db.no_autoflush:
        negativa = svc.primeira_data_negativa(db.query(MovimentoReserva).all())
    if negativa:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Com essa alteração a reserva ficaria negativa em {negativa:%d/%m/%Y}.",
        )
    db.commit()
    db.refresh(movimento)
    return movimento


@router.delete("/{movimento_id}", status_code=204)
def remover(db: Db, movimento_id: int):
    movimento = obter_ou_404(db, MovimentoReserva, movimento_id, "Movimento não encontrado")
    if movimento.tipo == "aporte":
        restantes = [m for m in db.query(MovimentoReserva).all() if m.id != movimento.id]
        if svc.primeira_data_negativa(restantes):
            raise HTTPException(
                status_code=400,
                detail="Remover este aporte deixaria a reserva negativa. Remova antes os saques.",
            )
    db.delete(movimento)
    db.commit()
