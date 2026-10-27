from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import extract
from sqlalchemy.orm import Session

from ..database import Db
from ..models import Divida, Transacao
from ..schemas import (
    EncerrarRecorrencia,
    TransacaoCreate,
    TransacaoOut,
    TransacaoUpdate,
    validar_parcela,
)
from ..services import recorrentes
from ..services.dividas import pago_vinculado, recalcular_status
from ._comum import formatar_real, obter_ou_404, validar_opcao

router = APIRouter(prefix="/api/transacoes", tags=["transacoes"])


def _validar_divida(db: Session, divida_id: int | None) -> None:
    if divida_id is not None:
        obter_ou_404(db, Divida, divida_id, "Dívida não encontrada")


def _erro(mensagem: str) -> HTTPException:
    return HTTPException(status_code=422, detail=mensagem)


def _validar(db: Session, t: Transacao) -> None:
    _validar_divida(db, t.divida_id)
    validar_opcao(db, "categoria", t.categoria)
    validar_opcao(db, "meio_pagamento", t.meio_pagamento)
    try:
        validar_parcela(t.parcela_atual, t.parcelas_total)
    except ValueError as erro:
        raise _erro(str(erro)) from erro
    t.valor = round(t.valor, 2)
    if t.valor <= 0:
        raise _erro("O valor precisa ser maior que zero.")
    if not 2000 <= t.data.year <= 2100:
        raise _erro("A data precisa estar entre os anos 2000 e 2100.")
    if t.parcela_atual is not None and t.recorrencia != "parcelado":
        raise _erro('"Parcela n de N" só vale para recorrência "Parcelado".')
    if t.divida_id is not None:
        if t.tipo != "quitacao":
            raise _erro("Só lançamentos do tipo Quitação podem ser vinculados a uma dívida.")
        _validar_quitacao(db, t)


def _validar_quitacao(db: Session, t: Transacao) -> None:
    if t.situacao != "concluido":
        return
    divida = db.get(Divida, t.divida_id)
    pago = divida.total_pago + pago_vinculado(db, divida.id, ignorar_id=t.id)
    falta = round(divida.valor_inicial - pago, 2)
    if t.valor > falta + 0.005:
        raise _erro(
            f'Esse pagamento passa do que falta da dívida "{divida.nome}": '
            f"faltam {formatar_real(max(falta, 0))}."
        )


@router.get("", response_model=list[TransacaoOut])
def listar(
    db: Db,
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
    tipo: str | None = None,
    categoria: str | None = None,
    situacao: str | None = None,
):
    query = db.query(Transacao)
    if mes is not None:
        query = query.filter(extract("month", Transacao.data) == mes)
    if ano is not None:
        query = query.filter(extract("year", Transacao.data) == ano)
    if tipo:
        query = query.filter(Transacao.tipo == tipo)
    if categoria:
        query = query.filter(Transacao.categoria == categoria)
    if situacao:
        query = query.filter(Transacao.situacao == situacao)
    return query.order_by(Transacao.data.asc(), Transacao.id.asc()).all()


@router.post("", response_model=TransacaoOut, status_code=201)
def criar(db: Db, payload: TransacaoCreate):
    transacao = Transacao(**payload.model_dump())
    with db.no_autoflush:
        _validar(db, transacao)
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    recalcular_status(db, transacao.divida_id)
    return transacao


@router.post("/gerar-recorrentes", response_model=list[TransacaoOut], status_code=201)
def gerar_recorrentes(
    db: Db, mes: int = Query(..., ge=1, le=12), ano: int = Query(..., ge=2000, le=2100)
):
    with recorrentes.trava_geracao:
        criadas = [recorrentes.nova_a_partir(p) for p in recorrentes.previsoes_do_mes(db, mes, ano)]
        db.add_all(criadas)
        db.commit()
    for t in criadas:
        db.refresh(t)
    return criadas


@router.post("/encerrar-recorrencia")
def encerrar_recorrencia(db: Db, payload: EncerrarRecorrencia):
    removidos = recorrentes.encerrar(
        db, payload.lancamento, payload.categoria, payload.mes, payload.ano
    )
    return {"removidos": removidos}


@router.get("/{transacao_id}", response_model=TransacaoOut)
def detalhar(db: Db, transacao_id: int):
    transacao = obter_ou_404(db, Transacao, transacao_id, "Transação não encontrada")
    return transacao


@router.patch("/{transacao_id}", response_model=TransacaoOut)
def atualizar(db: Db, transacao_id: int, payload: TransacaoUpdate):
    transacao = obter_ou_404(db, Transacao, transacao_id, "Transação não encontrada")
    dados = payload.model_dump(exclude_unset=True)
    divida_anterior = transacao.divida_id
    for campo, valor in dados.items():
        setattr(transacao, campo, valor)
    try:
        with db.no_autoflush:
            _validar(db, transacao)
    except HTTPException:
        db.rollback()
        raise
    db.commit()
    db.refresh(transacao)
    recalcular_status(db, transacao.divida_id)
    if divida_anterior != transacao.divida_id:
        recalcular_status(db, divida_anterior)
    return transacao


@router.delete("/{transacao_id}", status_code=204)
def remover(db: Db, transacao_id: int):
    transacao = obter_ou_404(db, Transacao, transacao_id, "Transação não encontrada")
    divida_id = transacao.divida_id
    db.delete(transacao)
    db.commit()
    recalcular_status(db, divida_id)
