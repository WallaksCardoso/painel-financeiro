from datetime import date

from fastapi import APIRouter, Query

from ..database import Db
from ..schemas import Projecao
from ..services.projecao import projetar

router = APIRouter(prefix="/api/projecao", tags=["projecao"])


@router.get("", response_model=Projecao)
def projecao(
    db: Db,
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
    meses: int = Query(12, ge=1, le=36),
):
    hoje = date.today()
    return projetar(db, mes or hoje.month, ano or hoje.year, meses)
