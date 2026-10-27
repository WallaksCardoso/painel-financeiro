import sys
from datetime import date

from sqlalchemy.orm import Session

from .database import SessionLocal, inicializar_banco
from .models import (
    Cartao,
    CompraCartao,
    Divida,
    FaturaPaga,
    MovimentoReserva,
    OrcamentoCategoria,
    PlanoMes,
    Transacao,
)
from .services.fatura import (
    avancar,
    calcular_fatura,
    data_da_compra_em_andamento,
    fatura_que_vence_em,
    vencimento,
)

MENSAIS = [
    ("Salário (1ª parcela)", "receita", "salario", 3200.00, 5, "transferencia"),
    ("Salário (2ª parcela)", "receita", "salario", 2100.00, 20, "transferencia"),
    ("Vale-alimentação", "beneficio", "comida", 900.00, 1, None),
    ("Aluguel", "despesa", "apartamento", 1350.00, 10, "pix"),
    ("Energia", "despesa", "apartamento", 185.40, 12, "debito_automatico"),
    ("Internet", "despesa", "internet", 99.90, 15, "debito_automatico"),
    ("Academia", "despesa", "saude", 110.00, 8, "pix"),
]

COMPRAS_CARTAO = [
    ("Streaming de vídeo", 39.90, 1, True, "assinaturas", None),
    ("Streaming de música", 21.90, 1, True, "assinaturas", None),
    ("Mercado do mês", 486.30, 1, False, "comida", 3),
    ("Farmácia", 72.45, 1, False, "saude", 6),
    ("Tênis de corrida", 459.90, 3, False, "roupas", 9),
]


def _data(ano: int, mes: int, dia: int) -> date:
    return date(ano, mes, min(dia, 28))


def popular(db: Session, hoje: date | None = None) -> None:
    hoje = hoje or date.today()
    meses = [avancar(hoje.month, hoje.year, -n) for n in (2, 1, 0)]

    for mes, ano in meses:
        for lancamento, tipo, categoria, valor, dia, meio in MENSAIS:
            data = _data(ano, mes, dia)
            db.add(
                Transacao(
                    lancamento=lancamento,
                    tipo=tipo,
                    categoria=categoria,
                    valor=valor,
                    data=data,
                    meio_pagamento=meio,
                    recorrencia="mensal",
                    situacao="concluido" if data <= hoje else "nao_iniciada",
                )
            )

    for i, (mes, ano) in enumerate(meses):
        data = _data(ano, mes, 7)
        db.add(
            Transacao(
                lancamento="Curso de inglês",
                tipo="despesa",
                categoria="crescimento",
                valor=240.00,
                data=data,
                meio_pagamento="boleto",
                recorrencia="parcelado",
                parcela_atual=i + 1,
                parcelas_total=6,
                situacao="concluido" if data <= hoje else "nao_iniciada",
            )
        )

    mes_atual, ano_atual = meses[-1]
    db.add(
        Transacao(
            lancamento="Revisão do carro",
            tipo="despesa",
            categoria="carro",
            valor=620.00,
            data=_data(ano_atual, mes_atual, 18),
            meio_pagamento="pix",
            recorrencia="eventual",
            situacao="nao_iniciada",
        )
    )
    db.add(
        Transacao(
            lancamento="Tesouro Selic",
            tipo="investimento",
            categoria="reserva",
            valor=300.00,
            data=_data(ano_atual, mes_atual, 6),
            meio_pagamento="transferencia",
            recorrencia="eventual",
            situacao="concluido",
        )
    )

    divida = Divida(
        nome="Empréstimo pessoal",
        valor_inicial=4800.00,
        total_pago=1200.00,
        prioridade="alta",
        observacao="Acordo em 12 parcelas de R$ 400.",
    )
    db.add(divida)
    db.flush()
    for mes, ano in meses[:2]:
        db.add(
            Transacao(
                lancamento="Parcela do empréstimo",
                tipo="quitacao",
                categoria="quitacao",
                valor=400.00,
                data=_data(ano, mes, 25),
                meio_pagamento="pix",
                recorrencia="mensal",
                situacao="concluido",
                divida_id=divida.id,
            )
        )

    cartao = Cartao(
        nome="Cartão principal",
        bandeira="Mastercard",
        limite=6000.00,
        dia_fechamento=3,
        dia_vencimento=10,
        cor="#1b7f8f",
    )
    db.add(cartao)
    db.flush()
    primeiro_mes, primeiro_ano = meses[0]
    for descricao, total, parcelas, assinatura, categoria, dias_atras in COMPRAS_CARTAO:
        if dias_atras is None:
            data = _data(primeiro_ano, primeiro_mes, 2)
        else:
            data = date.fromordinal(
                max(hoje.toordinal() - dias_atras, _data(ano_atual, mes_atual, 1).toordinal())
            )
        db.add(
            CompraCartao(
                cartao_id=cartao.id,
                descricao=descricao,
                valor_total=total,
                data_compra=data,
                parcelas=parcelas,
                recorrente=assinatura,
                categoria=categoria,
            )
        )
    for descricao, parcela, atual, total, categoria in [
        ("Notebook", 312.50, 7, 12, "crescimento"),
        ("Geladeira", 189.90, 9, 10, "apartamento"),
    ]:
        db.add(
            CompraCartao(
                cartao_id=cartao.id,
                descricao=descricao,
                valor_total=round(parcela * total, 2),
                data_compra=data_da_compra_em_andamento(atual, mes_atual, ano_atual),
                parcelas=total,
                categoria=categoria,
            )
        )

    db.flush()
    db.refresh(cartao)
    for mes, ano in meses:
        f_mes, f_ano = fatura_que_vence_em(cartao, mes, ano)
        vence = vencimento(cartao, f_mes, f_ano)
        if vence < hoje:
            total = calcular_fatura(db, cartao, f_mes, f_ano).total
            db.add(
                FaturaPaga(
                    cartao_id=cartao.id, mes=f_mes, ano=f_ano, pago_em=vence, valor_pago=total
                )
            )

    for descricao, valor, (mes, ano) in [
        ("Saldo inicial", 2500.00, meses[0]),
        ("Aporte do mês", 400.00, meses[1]),
        ("Aporte do mês", 400.00, meses[2]),
    ]:
        db.add(
            MovimentoReserva(
                descricao=descricao,
                tipo="aporte",
                valor=valor,
                data=_data(ano, mes, 6),
                origem="salario",
            )
        )

    for categoria, teto in [("comida", 700.00), ("saude", 250.00), ("lazer", 300.00)]:
        db.add(OrcamentoCategoria(mes=mes_atual, ano=ano_atual, categoria=categoria, teto=teto))
    db.add(
        PlanoMes(
            mes=mes_atual,
            ano=ano_atual,
            meta_descricao="Antecipar uma parcela do empréstimo",
            meta_valor=400.00,
            limite_cartao=900.00,
            anotacoes="Dados fictícios de demonstração.",
        )
    )
    db.commit()


def main() -> int:
    inicializar_banco()
    with SessionLocal() as db:
        if db.query(Transacao).first() or db.query(Cartao).first():
            print("O banco já tem dados; a demonstração só é carregada num banco vazio.")
            return 1
        popular(db)
    print("Dados de demonstração carregados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
