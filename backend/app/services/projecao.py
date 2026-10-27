from sqlalchemy import extract
from sqlalchemy.orm import Session

from ..models import Cartao, CompraCartao, Transacao
from ..schemas import LinhaProjecao, ParcelaAtiva, ParcelaTerminando, Projecao, ProjecaoMes
from .fatura import (
    avancar,
    fatura_que_vence_em,
    mes_referencia,
    parcela_no_mes,
    valores_parcelas,
    vencimento,
)
from .recorrentes import previsoes_do_mes

GRUPO_POR_TIPO = {
    "receita": "entrada",
    "despesa": "conta",
    "quitacao": "quitacao",
    "investimento": "investimento",
    "beneficio": "beneficio",
}


def _linhas_transacoes(db: Session, mes: int, ano: int) -> list[LinhaProjecao]:
    lancadas = (
        db.query(Transacao)
        .filter(
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano,
        )
        .all()
    )
    linhas = [
        LinhaProjecao(
            descricao=t.lancamento,
            grupo=GRUPO_POR_TIPO[t.tipo],
            valor=round(t.valor, 2),
            dia=t.data.day,
            previsto=False,
        )
        for t in lancadas
    ]
    linhas += [
        LinhaProjecao(
            descricao=p.molde.lancamento,
            grupo=GRUPO_POR_TIPO[p.molde.tipo],
            valor=round(p.molde.valor, 2),
            dia=p.data.day,
            previsto=True,
        )
        for p in previsoes_do_mes(db, mes, ano)
    ]
    return linhas


def _cartoes_no_mes(
    cartoes: list[Cartao], mes: int, ano: int
) -> tuple[list[LinhaProjecao], list[ParcelaTerminando]]:
    linhas: list[LinhaProjecao] = []
    terminando: list[ParcelaTerminando] = []
    for cartao in cartoes:
        f_mes, f_ano = fatura_que_vence_em(cartao, mes, ano)
        total = 0.0
        for compra in cartao.compras:
            parcela = parcela_no_mes(compra, cartao.dia_fechamento, f_mes, f_ano)
            if parcela is None:
                continue
            numero, valor = parcela
            total += valor
            if not compra.recorrente and compra.parcelas > 1 and numero == compra.parcelas:
                terminando.append(
                    ParcelaTerminando(
                        compra_id=compra.id,
                        descricao=compra.descricao,
                        cartao_nome=cartao.nome,
                        valor_parcela=valores_parcelas(compra.valor_total, compra.parcelas)[0],
                    )
                )
        if total > 0:
            linhas.append(
                LinhaProjecao(
                    descricao=f"Fatura {cartao.nome}",
                    grupo="cartao",
                    valor=round(total, 2),
                    dia=vencimento(cartao, f_mes, f_ano).day,
                    previsto=False,
                )
            )
    return linhas, terminando


def _parcelas_ativas(cartoes: list[Cartao], mes: int, ano: int) -> list[ParcelaAtiva]:
    ativas: list[ParcelaAtiva] = []
    for cartao in cartoes:
        f_mes, f_ano = fatura_que_vence_em(cartao, mes, ano)
        for compra in cartao.compras:
            if compra.recorrente or compra.parcelas <= 1:
                continue
            primeira_mes, primeira_ano = mes_referencia(compra.data_compra, cartao.dia_fechamento)
            ultima = _ultima_fatura(compra, cartao)
            if ultima < (f_ano, f_mes):
                continue
            atual = parcela_no_mes(compra, cartao.dia_fechamento, f_mes, f_ano)
            numero = atual[0] if atual else 0
            valor = valores_parcelas(compra.valor_total, compra.parcelas)[0]
            inicio = vencimento(cartao, primeira_mes, primeira_ano)
            fim = vencimento(cartao, ultima[1], ultima[0])
            ativas.append(
                ParcelaAtiva(
                    compra_id=compra.id,
                    descricao=compra.descricao,
                    cartao_nome=cartao.nome,
                    parcela_atual=numero,
                    parcelas_total=compra.parcelas,
                    valor_parcela=round(valor, 2),
                    comeca_mes=inicio.month,
                    comeca_ano=inicio.year,
                    termina_mes=fim.month,
                    termina_ano=fim.year,
                )
            )
    return sorted(ativas, key=lambda p: (p.termina_ano, p.termina_mes, p.descricao))


def _ultima_fatura(compra: CompraCartao, cartao: Cartao) -> tuple[int, int]:
    base_mes, base_ano = mes_referencia(compra.data_compra, cartao.dia_fechamento)
    m, a = avancar(base_mes, base_ano, compra.parcelas - 1)
    return a, m


def _sem_valor(db: Session, cartoes: list[Cartao]) -> list[str]:
    nomes = {c.descricao for cartao in cartoes for c in cartao.compras if c.valor_total <= 0}
    nomes |= {
        t.lancamento
        for t in db.query(Transacao).filter(Transacao.recorrencia == "mensal", Transacao.valor <= 0)
    }
    return sorted(nomes)


def projetar(db: Session, mes: int, ano: int, meses: int) -> Projecao:
    cartoes = db.query(Cartao).filter(Cartao.ativo.is_(True)).all()
    resultado: list[ProjecaoMes] = []
    acumulado = 0.0

    for i in range(meses):
        m, a = avancar(mes, ano, i)
        linhas = _linhas_transacoes(db, m, a)
        linhas_cartao, terminando = _cartoes_no_mes(cartoes, m, a)
        linhas += linhas_cartao
        linhas.sort(key=lambda linha: (linha.dia or 0, linha.descricao))

        def soma(grupo: str, linhas: list[LinhaProjecao] = linhas) -> float:
            return round(sum(linha.valor for linha in linhas if linha.grupo == grupo), 2)

        entradas = soma("entrada")
        saidas = round(soma("conta") + soma("quitacao") + soma("investimento") + soma("cartao"), 2)
        sobra = round(entradas - saidas, 2)
        acumulado = round(acumulado + sobra, 2)
        resultado.append(
            ProjecaoMes(
                mes=m,
                ano=a,
                entradas=entradas,
                contas=soma("conta"),
                quitacoes=soma("quitacao"),
                investimentos=soma("investimento"),
                cartao=soma("cartao"),
                saidas=saidas,
                sobra=sobra,
                acumulado=acumulado,
                linhas=linhas,
                terminando=terminando,
            )
        )

    return Projecao(
        meses=resultado,
        parcelas_ativas=_parcelas_ativas(cartoes, mes, ano),
        sem_valor=_sem_valor(db, cartoes),
    )
