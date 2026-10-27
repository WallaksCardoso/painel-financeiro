from datetime import date, timedelta

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from ..database import Db
from ..models import Cartao, Configuracao, Transacao
from ..schemas import (
    CategoriaTotal,
    DashboardCompleto,
    ProximaConta,
    ResumoMes,
)
from ..services import dividas, fatura, gastos, reserva
from ..services.projecao import projetar

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/resumo", response_model=ResumoMes)
def resumo(
    db: Db,
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
):
    hoje = date.today()
    m = projetar(db, mes or hoje.month, ano or hoje.year, 1).meses[0]
    return ResumoMes(
        mes=m.mes,
        ano=m.ano,
        entradas=m.entradas,
        saidas=m.contas,
        saldo=m.sobra,
        quitacoes=m.quitacoes,
        investimentos=m.investimentos,
        cartao=m.cartao,
    )


@router.get("/por-categoria", response_model=list[CategoriaTotal])
def por_categoria(
    db: Db,
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
    tipo: str = "despesa",
):
    hoje = date.today()
    mes = mes or hoje.month
    ano = ano or hoje.year

    totais = gastos.por_categoria(db, mes, ano, tipo)
    ordenados = sorted(totais.items(), key=lambda kv: kv[1], reverse=True)
    return [CategoriaTotal(categoria=c, total=t) for c, t in ordenados]


def _proximas(db: Session, dias: int) -> list[ProximaConta]:
    hoje = date.today()
    limite = hoje + timedelta(days=dias)
    pendentes = (
        db.query(Transacao)
        .filter(
            Transacao.tipo.in_(("despesa", "quitacao")),
            Transacao.situacao != "concluido",
            Transacao.data >= hoje,
            Transacao.data <= limite,
        )
        .all()
    )
    contas = [
        ProximaConta(
            id=f"t{t.id}",
            lancamento=t.lancamento,
            valor=t.valor,
            data=t.data,
            dias_ate_vencer=(t.data - hoje).days,
            categoria=t.categoria,
        )
        for t in pendentes
    ]
    for cartao in db.query(Cartao).filter(Cartao.ativo.is_(True)):
        m, a = hoje.month, hoje.year
        while date(a, m, 1) <= limite:
            f_mes, f_ano = fatura.fatura_que_vence_em(cartao, m, a)
            venc = fatura.vencimento(cartao, f_mes, f_ano)
            if hoje <= venc <= limite and not fatura.fatura_paga(db, cartao.id, f_mes, f_ano):
                total = fatura.calcular_fatura(db, cartao, f_mes, f_ano).total
                if total > 0:
                    contas.append(
                        ProximaConta(
                            id=f"c{cartao.id}-{f_ano}-{f_mes}",
                            lancamento=f"Fatura {cartao.nome}",
                            valor=total,
                            data=venc,
                            dias_ate_vencer=(venc - hoje).days,
                            categoria=None,
                        )
                    )
            m, a = fatura.avancar(m, a, 1)
    return sorted(contas, key=lambda c: (c.data, c.lancamento))


@router.get("/proximas", response_model=list[ProximaConta])
def proximas(db: Db, dias: int = Query(15, ge=1, le=60)):
    return _proximas(db, dias)


@router.get("/completo", response_model=DashboardCompleto)
def completo(
    db: Db,
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
):
    hoje = date.today()
    mes = mes or hoje.month
    ano = ano or hoje.year

    resumo_mes = resumo(db=db, mes=mes, ano=ano)
    categorias = por_categoria(db=db, mes=mes, ano=ano)
    config = db.get(Configuracao, "dias_proximas_contas")
    proximas_lista = _proximas(db, int(config.valor) if config else 15)

    return DashboardCompleto(
        resumo=resumo_mes,
        por_categoria=categorias,
        saldo_reserva=reserva.saldo(db),
        total_dividas_restante=dividas.total_restante(db),
        fatura_aberta=fatura.total_faturas_abertas(db, mes, ano),
        proximas_contas=proximas_lista,
    )
