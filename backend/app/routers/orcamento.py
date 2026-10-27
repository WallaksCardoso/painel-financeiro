from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import Db
from ..models import OrcamentoCategoria
from ..schemas import OrcamentoCreate, OrcamentoOut, OrcamentoUpdate
from ..services import gastos
from ._comum import obter_ou_404, validar_opcao

router = APIRouter(prefix="/api/orcamento", tags=["orcamento"])


def _garantir_unico(
    db: Session, mes: int, ano: int, categoria: str, ignorar_id: int | None = None
) -> None:
    query = db.query(OrcamentoCategoria).filter(
        OrcamentoCategoria.mes == mes,
        OrcamentoCategoria.ano == ano,
        OrcamentoCategoria.categoria == categoria,
    )
    if ignorar_id is not None:
        query = query.filter(OrcamentoCategoria.id != ignorar_id)
    if query.first():
        raise HTTPException(
            status_code=409, detail="Já existe um teto para essa categoria nesse mês"
        )


def _serializar(item: OrcamentoCategoria, gasto: float) -> OrcamentoOut:
    restante = round(item.teto - gasto, 2)
    uso = round(gasto / item.teto * 100, 1) if item.teto > 0 else 0.0

    if item.teto == 0:
        status = "estourou" if gasto > 0 else "ok"
        uso = 100.0 if gasto > 0 else 0.0
    elif uso > 100:
        status = "estourou"
    elif uso > 80:
        status = "atencao"
    else:
        status = "ok"

    return OrcamentoOut(
        id=item.id,
        mes=item.mes,
        ano=item.ano,
        categoria=item.categoria,
        teto=item.teto,
        gasto=gasto,
        restante=restante,
        uso_percentual=uso,
        status=status,
    )


def _serializar_varios(itens: list[OrcamentoCategoria], db: Session) -> list[OrcamentoOut]:
    cache: dict[tuple[int, int], dict[str, float]] = {}
    resultado = []
    for item in itens:
        chave = (item.mes, item.ano)
        if chave not in cache:
            cache[chave] = gastos.por_categoria(db, item.mes, item.ano)
        resultado.append(_serializar(item, cache[chave].get(item.categoria, 0.0)))
    return resultado


@router.get("", response_model=list[OrcamentoOut])
def listar(
    db: Db,
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
):
    query = db.query(OrcamentoCategoria)
    if mes is not None:
        query = query.filter(OrcamentoCategoria.mes == mes)
    if ano is not None:
        query = query.filter(OrcamentoCategoria.ano == ano)
    return _serializar_varios(query.order_by(OrcamentoCategoria.categoria.asc()).all(), db)


@router.post("", response_model=OrcamentoOut, status_code=201)
def criar(db: Db, payload: OrcamentoCreate):
    validar_opcao(db, "categoria", payload.categoria)
    _garantir_unico(db, payload.mes, payload.ano, payload.categoria)
    item = OrcamentoCategoria(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serializar_varios([item], db)[0]


@router.patch("/{item_id}", response_model=OrcamentoOut)
def atualizar(db: Db, item_id: int, payload: OrcamentoUpdate):
    item = obter_ou_404(db, OrcamentoCategoria, item_id, "Item de orçamento não encontrado")
    dados = payload.model_dump(exclude_unset=True)
    validar_opcao(db, "categoria", dados.get("categoria"))
    _garantir_unico(
        db,
        dados.get("mes", item.mes),
        dados.get("ano", item.ano),
        dados.get("categoria", item.categoria),
        ignorar_id=item.id,
    )
    for campo, valor in dados.items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return _serializar_varios([item], db)[0]


@router.delete("/{item_id}", status_code=204)
def remover(db: Db, item_id: int):
    db.delete(obter_ou_404(db, OrcamentoCategoria, item_id, "Item de orçamento não encontrado"))
    db.commit()
