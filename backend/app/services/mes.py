from sqlalchemy import extract
from sqlalchemy.orm import Session

from ..models import Cartao, FaturaPaga, Opcao, PlanoMes, Transacao
from ..schemas import ItemMes, PlanoMesOut, ResumoMesPlano
from .fatura import fatura_que_vence_em, parcela_no_mes, vencimento
from .recorrentes import Previsao, previsoes_do_mes

QUANTIDADE_POR_RECORRENCIA = {"mensal": "Fixo", "parcelado": "Parcelado", "eventual": "Eventual"}


def plano_do_mes(db: Session, mes: int, ano: int) -> PlanoMesOut:
    plano = db.query(PlanoMes).filter(PlanoMes.mes == mes, PlanoMes.ano == ano).first()
    if plano is None:
        return PlanoMesOut(mes=mes, ano=ano, salvo=False)
    return PlanoMesOut(
        mes=mes,
        ano=ano,
        salvo=True,
        meta_descricao=plano.meta_descricao,
        meta_valor=plano.meta_valor,
        limite_cartao=plano.limite_cartao,
        anotacoes=plano.anotacoes,
    )


def _quantidade(t: Transacao, parcela_atual: int | None) -> str:
    if t.tipo == "quitacao":
        return "Dívida"
    if t.recorrencia == "parcelado" and parcela_atual and t.parcelas_total:
        return f"{parcela_atual}/{t.parcelas_total}"
    return QUANTIDADE_POR_RECORRENCIA.get(t.recorrencia, "")


def _item_lancado(t: Transacao, meios: dict[str, str]) -> ItemMes:
    return ItemMes(
        origem="transacao",
        tipo=t.tipo,
        id=t.id,
        recorrencia=t.recorrencia,
        descricao=t.lancamento,
        valor=round(t.valor, 2),
        dia=t.data.day,
        quantidade=_quantidade(t, t.parcela_atual),
        meio=meios.get(t.meio_pagamento or "", t.meio_pagamento),
        situacao=t.situacao,
        categoria=t.categoria,
        observacao=t.observacao,
    )


def _item_previsto(p: Previsao, meios: dict[str, str]) -> ItemMes:
    m = p.molde
    return ItemMes(
        origem="previsto",
        tipo=m.tipo,
        id=None,
        molde_id=m.id,
        recorrencia=m.recorrencia,
        descricao=m.lancamento,
        valor=round(m.valor, 2),
        dia=p.data.day,
        quantidade=_quantidade(m, p.parcela_atual),
        meio=meios.get(m.meio_pagamento or "", m.meio_pagamento),
        situacao="nao_iniciada",
        categoria=m.categoria,
        observacao=None,
    )


def _transacoes(db: Session, mes: int, ano: int, meios: dict[str, str]) -> list[ItemMes]:
    lancadas = (
        db.query(Transacao)
        .filter(
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano,
        )
        .all()
    )
    itens = [_item_lancado(t, meios) for t in lancadas]
    itens += [_item_previsto(p, meios) for p in previsoes_do_mes(db, mes, ano)]
    return sorted(itens, key=lambda i: (i.dia or 0, i.descricao))


def resumo_do_mes(db: Session, mes: int, ano: int) -> ResumoMesPlano:
    meios = {o.chave: o.nome for o in db.query(Opcao).filter(Opcao.grupo == "meio_pagamento")}

    itens = _transacoes(db, mes, ano, meios)
    receitas = [i for i in itens if i.tipo == "receita"]
    beneficios = [i for i in itens if i.tipo == "beneficio"]
    dividas = [i for i in itens if i.tipo == "quitacao"]
    contas = [i for i in itens if i.tipo in ("despesa", "investimento")]

    fixos_cartao: list[ItemMes] = []
    cartao_variavel = 0.0
    for cartao in db.query(Cartao).filter(Cartao.ativo.is_(True)).all():
        f_mes, f_ano = fatura_que_vence_em(cartao, mes, ano)
        dia_venc = vencimento(cartao, f_mes, f_ano).day
        paga = (
            db.query(FaturaPaga)
            .filter(
                FaturaPaga.cartao_id == cartao.id, FaturaPaga.mes == f_mes, FaturaPaga.ano == f_ano
            )
            .first()
        )
        for compra in cartao.compras:
            parcela = parcela_no_mes(compra, cartao.dia_fechamento, f_mes, f_ano)
            if parcela is None:
                continue
            numero, valor = parcela
            if not compra.recorrente and compra.parcelas <= 1:
                cartao_variavel += valor
                continue
            fixos_cartao.append(
                ItemMes(
                    origem="compra",
                    tipo="cartao",
                    id=compra.id,
                    descricao=compra.descricao,
                    valor=valor if valor > 0 else None,
                    dia=dia_venc,
                    quantidade="Fixo" if compra.recorrente else f"{numero}/{compra.parcelas}",
                    meio=f"Cartão {cartao.nome}",
                    situacao="concluido" if paga else "nao_iniciada",
                    categoria=compra.categoria,
                    observacao=compra.observacao,
                )
            )

    def soma(lista: list[ItemMes]) -> float:
        return round(sum(i.valor or 0 for i in lista), 2)

    contas_fixas = [i for i in contas if i.tipo == "despesa" and i.recorrencia != "eventual"]
    outras_lista = [i for i in contas if i not in contas_fixas]
    fixo_conta = soma(contas_fixas)
    fixo_cartao = soma(fixos_cartao)
    gasto_fixo = round(fixo_conta + fixo_cartao, 2)
    outras = soma(outras_lista)
    total_receitas = soma(receitas)
    total_dividas = soma(dividas)
    cartao_variavel = round(cartao_variavel, 2)

    primeira = min(receitas, key=lambda i: i.dia or 0, default=None)
    fixos = sorted(contas_fixas + fixos_cartao, key=lambda i: (i.dia or 0, i.descricao))

    return ResumoMesPlano(
        mes=mes,
        ano=ano,
        plano=plano_do_mes(db, mes, ano),
        receitas=receitas,
        beneficios=beneficios,
        fixos=fixos,
        outras=outras_lista,
        dividas=dividas,
        total_receitas=total_receitas,
        total_beneficios=soma(beneficios),
        fixo_conta=fixo_conta,
        fixo_cartao=fixo_cartao,
        gasto_fixo=gasto_fixo,
        outras_despesas=outras,
        total_dividas=total_dividas,
        cartao_variavel=cartao_variavel,
        primeira_entrada=primeira,
        sobra_primeira_entrada=round((primeira.valor or 0) - gasto_fixo, 2) if primeira else None,
        livre=round(total_receitas - gasto_fixo - outras - total_dividas - cartao_variavel, 2),
        previstos=sum(1 for i in itens if i.origem == "previsto"),
    )
