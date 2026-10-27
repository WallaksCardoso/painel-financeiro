from fastapi import APIRouter, Path

from ..database import Db
from ..models import PlanoMes
from ..schemas import PlanoMesIn, PlanoMesOut, ResumoMesPlano
from ..services import mes as svc

router = APIRouter(prefix="/api/mes", tags=["mes"])

Ano = Path(ge=2000, le=2100)
Mes = Path(ge=1, le=12)


@router.get("/{ano}/{mes}", response_model=ResumoMesPlano)
def resumo(db: Db, ano: int = Ano, mes: int = Mes):
    return svc.resumo_do_mes(db, mes, ano)


@router.put("/{ano}/{mes}/plano", response_model=PlanoMesOut)
def salvar_plano(db: Db, payload: PlanoMesIn, ano: int = Ano, mes: int = Mes):
    plano = db.query(PlanoMes).filter(PlanoMes.mes == mes, PlanoMes.ano == ano).first()
    if plano is None:
        plano = PlanoMes(mes=mes, ano=ano)
        db.add(plano)
    for campo, valor in payload.model_dump().items():
        setattr(plano, campo, valor)
    db.commit()
    return svc.plano_do_mes(db, mes, ano)
