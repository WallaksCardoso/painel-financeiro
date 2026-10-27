from fastapi import APIRouter, HTTPException
from sqlalchemy import case
from sqlalchemy.orm import Session

from ..database import Db
from ..models import Divida, Transacao
from ..schemas import DividaCreate, DividaOut, DividaUpdate
from ..services import dividas as svc
from ._comum import formatar_real, obter_ou_404

router = APIRouter(prefix="/api/dividas", tags=["dividas"])


def _serializar(divida: Divida, vinculado: float) -> DividaOut:
    efetivo = round(divida.total_pago + vinculado, 2)
    progresso = 0.0
    if divida.valor_inicial > 0:
        progresso = round(min(efetivo / divida.valor_inicial * 100, 100), 1)
    return DividaOut(
        id=divida.id,
        nome=divida.nome,
        valor_inicial=divida.valor_inicial,
        total_pago=divida.total_pago,
        prazo=divida.prazo,
        status=divida.status,
        prioridade=divida.prioridade,
        observacao=divida.observacao,
        criado_em=divida.criado_em,
        pago_vinculado=vinculado,
        pago_efetivo=efetivo,
        restante=svc.restante(divida, vinculado),
        progresso=progresso,
    )


def _serializar_uma(divida: Divida, db: Session) -> DividaOut:
    return _serializar(divida, svc.pago_vinculado(db, divida.id))


@router.get("", response_model=list[DividaOut])
def listar(db: Db):
    peso = case({"alta": 0, "media": 1, "baixa": 2}, value=Divida.prioridade, else_=3)
    dividas = db.query(Divida).order_by(peso, Divida.id.asc()).all()
    vinculados = svc.pagos_vinculados(db)
    return [_serializar(d, vinculados.get(d.id, 0.0)) for d in dividas]


@router.post("", response_model=DividaOut, status_code=201)
def criar(db: Db, payload: DividaCreate):
    divida = Divida(**payload.model_dump())
    db.add(divida)
    db.commit()
    if payload.status != "concluido":
        svc.recalcular_status(db, divida.id)
    db.refresh(divida)
    return _serializar_uma(divida, db)


@router.patch("/{divida_id}", response_model=DividaOut)
def atualizar(db: Db, divida_id: int, payload: DividaUpdate):
    divida = obter_ou_404(db, Divida, divida_id, "Dívida não encontrada")
    dados = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(divida, campo, valor)
    vinculado = svc.pago_vinculado(db, divida.id)
    if divida.total_pago + vinculado > divida.valor_inicial + 0.005:
        db.rollback()
        detalhe = "O valor já pago não pode ser maior que o valor da dívida."
        if vinculado:
            detalhe += f" Já há {formatar_real(vinculado)} em quitações registradas."
        raise HTTPException(status_code=422, detail=detalhe)
    db.commit()
    if "status" not in dados:
        svc.recalcular_status(db, divida.id)
    db.refresh(divida)
    return _serializar_uma(divida, db)


@router.delete("/{divida_id}", status_code=204)
def remover(db: Db, divida_id: int):
    divida = obter_ou_404(db, Divida, divida_id, "Dívida não encontrada")
    db.query(Transacao).filter(Transacao.divida_id == divida_id).update({Transacao.divida_id: None})
    db.delete(divida)
    db.commit()
