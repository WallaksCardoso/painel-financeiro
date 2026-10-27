from datetime import date

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import Db
from ..models import Cartao, CompraCartao, FaturaPaga
from ..schemas import (
    CartaoCreate,
    CartaoOut,
    CartaoUpdate,
    CompraCartaoCreate,
    CompraCartaoOut,
    CompraCartaoUpdate,
    CompraEmAndamentoCreate,
    FaturaMes,
    FaturaPagaCreate,
    FaturaPagaOut,
    validar_compra,
)
from ..services import fatura as svc
from ..services.opcoes import gerar_chave
from ._comum import obter_ou_404, validar_opcao

router = APIRouter(prefix="/api/cartoes", tags=["cartoes"])


def _serializar_compra(c: CompraCartao, avisos: list[str] | None = None) -> CompraCartaoOut:
    primeira_mes, primeira_ano = svc.mes_referencia(c.data_compra, c.cartao.dia_fechamento)
    return CompraCartaoOut(
        id=c.id,
        cartao_id=c.cartao_id,
        descricao=c.descricao,
        valor_total=c.valor_total,
        data_compra=c.data_compra,
        parcelas=c.parcelas,
        categoria=c.categoria,
        recorrente=c.recorrente,
        tags=c.tags,
        observacao=c.observacao,
        criado_em=c.criado_em,
        valor_parcela=svc.valores_parcelas(c.valor_total, c.parcelas)[0],
        primeira_fatura_mes=primeira_mes,
        primeira_fatura_ano=primeira_ano,
        avisos=avisos or [],
    )


def _validar_compra(db: Session, compra: CompraCartao) -> None:
    try:
        obter_ou_404(db, Cartao, compra.cartao_id, "Cartão não encontrado")
        validar_opcao(db, "categoria", compra.categoria)
        try:
            validar_compra(compra.recorrente, compra.valor_total, compra.parcelas)
        except ValueError as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from erro
    except HTTPException:
        db.rollback()
        raise


def _salvar_compra(db: Session, compra: CompraCartao) -> CompraCartaoOut:
    db.commit()
    db.refresh(compra)
    return _serializar_compra(compra, svc.avisos_faturas_pagas(db, compra))


def _aplicar_em_andamento(
    db: Session, compra: CompraCartao, payload: CompraEmAndamentoCreate
) -> None:
    cartao = obter_ou_404(db, Cartao, payload.cartao_id, "Cartão não encontrado")
    mes, ano = payload.mes, payload.ano
    if payload.vence_em:
        mes, ano = svc.fatura_que_vence_em(cartao, mes, ano)
    compra.cartao_id = payload.cartao_id
    compra.descricao = payload.descricao
    compra.valor_total = round(payload.valor_parcela * payload.parcelas_total, 2)
    compra.data_compra = svc.data_da_compra_em_andamento(payload.parcela_atual, mes, ano)
    compra.parcelas = payload.parcelas_total
    compra.categoria = payload.categoria
    compra.recorrente = False
    compra.tags = payload.tags
    compra.observacao = payload.observacao


@router.get("", response_model=list[CartaoOut])
def listar(db: Db):
    return db.query(Cartao).order_by(Cartao.ativo.desc(), Cartao.nome.asc()).all()


def _garantir_nome_unico(db: Session, nome: str, ignorar_id: int | None = None) -> None:
    alvo = gerar_chave(nome)
    for c in db.query(Cartao):
        if c.id != ignorar_id and gerar_chave(c.nome) == alvo:
            raise HTTPException(status_code=409, detail=f'Já existe um cartão "{c.nome}"')


@router.post("", response_model=CartaoOut, status_code=201)
def criar(db: Db, payload: CartaoCreate):
    _garantir_nome_unico(db, payload.nome)
    cartao = Cartao(**payload.model_dump())
    db.add(cartao)
    db.commit()
    db.refresh(cartao)
    return cartao


@router.patch("/{cartao_id}", response_model=CartaoOut)
def atualizar(db: Db, cartao_id: int, payload: CartaoUpdate):
    cartao = obter_ou_404(db, Cartao, cartao_id, "Cartão não encontrado")
    dados = payload.model_dump(exclude_unset=True)
    if "nome" in dados:
        _garantir_nome_unico(db, dados["nome"], ignorar_id=cartao.id)
    for campo, valor in dados.items():
        setattr(cartao, campo, valor)
    db.commit()
    db.refresh(cartao)
    return cartao


@router.delete("/{cartao_id}", status_code=204)
def remover(db: Db, cartao_id: int):
    db.delete(obter_ou_404(db, Cartao, cartao_id, "Cartão não encontrado"))
    db.commit()


@router.get("/compras", response_model=list[CompraCartaoOut])
def listar_compras(db: Db, cartao_id: int | None = Query(None)):
    query = db.query(CompraCartao)
    if cartao_id is not None:
        query = query.filter(CompraCartao.cartao_id == cartao_id)
    compras = query.order_by(CompraCartao.data_compra.desc()).all()
    return [_serializar_compra(c) for c in compras]


@router.post("/compras", response_model=CompraCartaoOut, status_code=201)
def criar_compra(db: Db, payload: CompraCartaoCreate):
    compra = CompraCartao(**payload.model_dump())
    _validar_compra(db, compra)
    db.add(compra)
    return _salvar_compra(db, compra)


@router.post("/compras/em-andamento", response_model=CompraCartaoOut, status_code=201)
def criar_compra_em_andamento(db: Db, payload: CompraEmAndamentoCreate):
    compra = CompraCartao()
    _aplicar_em_andamento(db, compra, payload)
    _validar_compra(db, compra)
    db.add(compra)
    return _salvar_compra(db, compra)


@router.put("/compras/{compra_id}/em-andamento", response_model=CompraCartaoOut)
def atualizar_compra_em_andamento(db: Db, compra_id: int, payload: CompraEmAndamentoCreate):
    compra = obter_ou_404(db, CompraCartao, compra_id, "Compra não encontrada")
    _aplicar_em_andamento(db, compra, payload)
    _validar_compra(db, compra)
    return _salvar_compra(db, compra)


@router.patch("/compras/{compra_id}", response_model=CompraCartaoOut)
def atualizar_compra(db: Db, compra_id: int, payload: CompraCartaoUpdate):
    compra = obter_ou_404(db, CompraCartao, compra_id, "Compra não encontrada")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(compra, campo, valor)
    _validar_compra(db, compra)
    return _salvar_compra(db, compra)


@router.delete("/compras/{compra_id}", status_code=204)
def remover_compra(db: Db, compra_id: int):
    db.delete(obter_ou_404(db, CompraCartao, compra_id, "Compra não encontrada"))
    db.commit()


@router.get("/{cartao_id}/fatura", response_model=FaturaMes)
def fatura(
    db: Db,
    cartao_id: int,
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    vence_em: bool = Query(False, description="mes/ano é o mês do vencimento, não do fechamento"),
):
    cartao = obter_ou_404(db, Cartao, cartao_id, "Cartão não encontrado")
    if vence_em:
        mes, ano = svc.fatura_que_vence_em(cartao, mes, ano)
    return svc.calcular_fatura(db, cartao, mes, ano)


@router.post("/{cartao_id}/faturas", response_model=FaturaPagaOut, status_code=201)
def marcar_fatura_paga(db: Db, cartao_id: int, payload: FaturaPagaCreate):
    obter_ou_404(db, Cartao, cartao_id, "Cartão não encontrado")
    if svc.fatura_paga(db, cartao_id, payload.mes, payload.ano):
        raise HTTPException(status_code=409, detail="Esta fatura já está marcada como paga")

    paga = FaturaPaga(
        cartao_id=cartao_id,
        mes=payload.mes,
        ano=payload.ano,
        pago_em=payload.pago_em or date.today(),
        valor_pago=payload.valor_pago,
        observacao=payload.observacao,
    )
    db.add(paga)
    db.commit()
    db.refresh(paga)
    return paga


@router.delete("/faturas/{fatura_paga_id}", status_code=204)
def desmarcar_fatura_paga(db: Db, fatura_paga_id: int):
    db.delete(obter_ou_404(db, FaturaPaga, fatura_paga_id, "Pagamento não encontrado"))
    db.commit()
