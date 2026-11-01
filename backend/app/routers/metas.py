from fastapi import APIRouter, HTTPException

from ..database import Db
from ..models import MetaPoupanca
from ..schemas import MetaPoupancaIn, MetaPoupancaOut
from ._comum import obter_ou_404

router = APIRouter(prefix="/api/metas", tags=["metas"])

NAO_ENCONTRADA = "Meta não encontrada"


def _conflito(db: Db, payload: MetaPoupancaIn, ignorar: int | None = None) -> None:
    existente = (
        db.query(MetaPoupanca)
        .filter(MetaPoupanca.mes == payload.mes, MetaPoupanca.ano == payload.ano)
        .first()
    )
    if existente is not None and existente.id != ignorar:
        raise HTTPException(
            status_code=409, detail="Já existe uma meta começando neste mês. Edite a existente."
        )


@router.get("", response_model=list[MetaPoupancaOut])
def listar(db: Db):
    return db.query(MetaPoupanca).order_by(MetaPoupanca.ano, MetaPoupanca.mes).all()


@router.post("", response_model=MetaPoupancaOut, status_code=201)
def criar(db: Db, payload: MetaPoupancaIn):
    _conflito(db, payload)
    meta = MetaPoupanca(**payload.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta


@router.put("/{meta_id}", response_model=MetaPoupancaOut)
def atualizar(db: Db, meta_id: int, payload: MetaPoupancaIn):
    meta = obter_ou_404(db, MetaPoupanca, meta_id, NAO_ENCONTRADA)
    _conflito(db, payload, ignorar=meta_id)
    for campo, valor in payload.model_dump().items():
        setattr(meta, campo, valor)
    db.commit()
    db.refresh(meta)
    return meta


@router.delete("/{meta_id}", status_code=204)
def remover(db: Db, meta_id: int):
    meta = obter_ou_404(db, MetaPoupanca, meta_id, NAO_ENCONTRADA)
    db.delete(meta)
    db.commit()
