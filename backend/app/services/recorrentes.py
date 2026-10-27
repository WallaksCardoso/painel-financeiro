import threading
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import extract
from sqlalchemy.orm import Session

from ..models import Transacao

RECORRENCIAS_QUE_REPETEM = ("mensal", "parcelado")

trava_geracao = threading.Lock()


@dataclass
class Previsao:
    molde: Transacao
    data: date
    parcela_atual: int | None = None


def chave(t: Transacao) -> tuple[str, str]:
    return t.lancamento, t.categoria


def _meses_entre(de: date, ate: date) -> int:
    return (ate.year - de.year) * 12 + (ate.month - de.month)


def _pascoa(ano: int) -> date:
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    dia_semana = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * dia_semana) // 433
    mes = (h + dia_semana - 7 * m + 90) // 25
    return date(ano, mes, (h + dia_semana - 7 * m + 33 * mes + 19) % 32)


def _feriados(ano: int) -> set[date]:
    fixos = [(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (11, 20), (12, 25)]
    pascoa = _pascoa(ano)
    moveis = {pascoa + timedelta(days=n) for n in (-48, -47, -2, 60)}
    return {date(ano, m, d) for m, d in fixos} | moveis


def _dia_util(dia: date, para_tras: bool) -> date:
    passo = timedelta(days=-1 if para_tras else 1)
    while dia.weekday() >= 5 or dia in _feriados(dia.year):
        dia += passo
    return dia


def _no_dia_util(dia: date, antecipa: bool) -> date:
    ajustado = _dia_util(dia, antecipa)
    if ajustado.month != dia.month:
        ajustado = _dia_util(dia, not antecipa)
    return ajustado


def _dia_habitual(datas: list[date], tipo: str) -> int:
    antecipa = tipo in ("receita", "beneficio")

    def explica(dia: int, d: date) -> bool:
        nominal = d.replace(day=min(dia, monthrange(d.year, d.month)[1]))
        return _no_dia_util(nominal, antecipa) == d or nominal == d

    candidatos = list(dict.fromkeys(d.day for d in datas))
    return max(candidatos, key=lambda dia: sum(explica(dia, d) for d in datas))


def previsoes_do_mes(db: Session, mes: int, ano: int) -> list[Previsao]:
    inicio = date(ano, mes, 1)
    anteriores = (
        db.query(Transacao)
        .filter(
            Transacao.recorrencia.in_(RECORRENCIAS_QUE_REPETEM),
            Transacao.data < inicio,
        )
        .order_by(Transacao.data.desc(), Transacao.id.desc())
        .all()
    )
    ja_no_mes = {
        chave(t)
        for t in db.query(Transacao).filter(
            Transacao.recorrencia.in_(RECORRENCIAS_QUE_REPETEM),
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano,
        )
    }

    datas_por_chave: dict[tuple[str, str], list[date]] = {}
    for t in anteriores:
        datas_por_chave.setdefault(chave(t), []).append(t.data)

    previsoes: list[Previsao] = []
    vistos: set[tuple[str, str]] = set()
    for molde in anteriores:
        k = chave(molde)
        if k in vistos:
            continue
        vistos.add(k)
        if k in ja_no_mes:
            continue
        if molde.recorrente_ate is not None and inicio > molde.recorrente_ate:
            continue

        parcela = None
        if molde.recorrencia == "parcelado":
            if not molde.parcela_atual or not molde.parcelas_total:
                continue
            parcela = molde.parcela_atual + _meses_entre(molde.data, inicio)
            if parcela > molde.parcelas_total:
                continue

        dia = min(_dia_habitual(datas_por_chave[k], molde.tipo), monthrange(ano, mes)[1])
        data = _no_dia_util(date(ano, mes, dia), antecipa=molde.tipo in ("receita", "beneficio"))
        previsoes.append(Previsao(molde=molde, data=data, parcela_atual=parcela))
    return sorted(previsoes, key=lambda p: (p.data, p.molde.lancamento))


def nova_a_partir(previsao: Previsao) -> Transacao:
    m = previsao.molde
    return Transacao(
        lancamento=m.lancamento,
        tipo=m.tipo,
        categoria=m.categoria,
        valor=m.valor,
        data=previsao.data,
        meio_pagamento=m.meio_pagamento,
        situacao="nao_iniciada",
        recorrencia=m.recorrencia,
        divida_id=m.divida_id,
        parcela_atual=previsao.parcela_atual,
        parcelas_total=m.parcelas_total if previsao.parcela_atual else None,
    )


def encerrar(db: Session, lancamento: str, categoria: str, ultimo_mes: int, ultimo_ano: int) -> int:
    ate = date(ultimo_ano, ultimo_mes, monthrange(ultimo_ano, ultimo_mes)[1])
    da_chave = db.query(Transacao).filter(
        Transacao.lancamento == lancamento,
        Transacao.categoria == categoria,
        Transacao.recorrencia.in_(RECORRENCIAS_QUE_REPETEM),
    )
    removidos = 0
    for t in da_chave.all():
        if t.data > ate and t.situacao != "concluido":
            db.delete(t)
            removidos += 1
        else:
            t.recorrente_ate = ate
    db.commit()
    return removidos
