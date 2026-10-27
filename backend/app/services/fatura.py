from calendar import monthrange
from collections.abc import Iterable, Iterator
from datetime import date

from sqlalchemy.orm import Session

from ..models import Cartao, CompraCartao, FaturaPaga
from ..schemas import FaturaMes, ItemFatura


def avancar(mes: int, ano: int, passos: int) -> tuple[int, int]:
    total = (ano * 12 + (mes - 1)) + passos
    return (total % 12) + 1, total // 12


def valores_parcelas(valor_total: float, parcelas: int) -> list[float]:
    parcelas = max(parcelas, 1)
    centavos = round(valor_total * 100)
    base, sobra = divmod(centavos, parcelas)
    return [(base + (1 if i >= parcelas - sobra else 0)) / 100 for i in range(parcelas)]


def mes_referencia(data_compra: date, dia_fechamento: int) -> tuple[int, int]:
    if data_compra.day > dia_fechamento:
        return avancar(data_compra.month, data_compra.year, 1)
    return data_compra.month, data_compra.year


def data_da_compra_em_andamento(parcela_atual: int, mes: int, ano: int) -> date:
    m, a = avancar(mes, ano, -(parcela_atual - 1))
    return date(a, m, 1)


def parcela_no_mes(
    compra: CompraCartao, dia_fechamento: int, mes: int, ano: int
) -> tuple[int, float] | None:
    base_mes, base_ano = mes_referencia(compra.data_compra, dia_fechamento)
    if compra.recorrente:
        if (ano, mes) >= (base_ano, base_mes):
            return 1, round(compra.valor_total, 2)
        return None
    indice = (ano * 12 + mes) - (base_ano * 12 + base_mes)
    if 0 <= indice < compra.parcelas:
        return indice + 1, valores_parcelas(compra.valor_total, compra.parcelas)[indice]
    return None


def vencimento(cartao: Cartao, mes: int, ano: int) -> date:
    if cartao.dia_vencimento <= cartao.dia_fechamento:
        mes, ano = avancar(mes, ano, 1)
    return date(ano, mes, min(cartao.dia_vencimento, monthrange(ano, mes)[1]))


def fatura_que_vence_em(cartao: Cartao, mes: int, ano: int) -> tuple[int, int]:
    if cartao.dia_vencimento <= cartao.dia_fechamento:
        return avancar(mes, ano, -1)
    return mes, ano


def eh_fixa(compra: CompraCartao) -> bool:
    return compra.recorrente or compra.parcelas > 1


def fatura_paga(db: Session, cartao_id: int, mes: int, ano: int) -> FaturaPaga | None:
    return (
        db.query(FaturaPaga)
        .filter(FaturaPaga.cartao_id == cartao_id, FaturaPaga.mes == mes, FaturaPaga.ano == ano)
        .first()
    )


def calcular_fatura(db: Session, cartao: Cartao, mes: int, ano: int) -> FaturaMes:
    itens: list[ItemFatura] = []
    total = total_fixo = total_variavel = total_comprometido_futuro = 0.0

    for compra in cartao.compras:
        resultado = parcela_no_mes(compra, cartao.dia_fechamento, mes, ano)
        if resultado is None:
            primeira = mes_referencia(compra.data_compra, cartao.dia_fechamento)
            if not compra.recorrente and (primeira[1], primeira[0]) > (ano, mes):
                total_comprometido_futuro += compra.valor_total
            continue
        parcela_atual, valor_parcela = resultado
        parcelas_restantes = compra.parcelas - parcela_atual

        itens.append(
            ItemFatura(
                compra_id=compra.id,
                descricao=compra.descricao,
                categoria=compra.categoria,
                parcela_atual=parcela_atual,
                parcelas_total=compra.parcelas,
                parcelas_restantes=parcelas_restantes,
                valor_parcela=valor_parcela,
                data_compra=compra.data_compra,
                recorrente=compra.recorrente,
                tags=compra.tags,
            )
        )
        total += valor_parcela
        if eh_fixa(compra):
            total_fixo += valor_parcela
        else:
            total_variavel += valor_parcela
        if not compra.recorrente and parcelas_restantes > 0:
            valores = valores_parcelas(compra.valor_total, compra.parcelas)
            total_comprometido_futuro += sum(valores[parcela_atual:])

    paga = fatura_paga(db, cartao.id, mes, ano)
    return FaturaMes(
        cartao_id=cartao.id,
        cartao_nome=cartao.nome,
        mes=mes,
        ano=ano,
        vencimento=vencimento(cartao, mes, ano),
        total=round(total, 2),
        total_fixo=round(total_fixo, 2),
        total_variavel=round(total_variavel, 2),
        total_comprometido_futuro=round(total_comprometido_futuro, 2),
        itens=itens,
        pago=paga is not None,
        fatura_paga_id=paga.id if paga else None,
        pago_em=paga.pago_em if paga else None,
        valor_pago=paga.valor_pago if paga else None,
    )


def _parcelas_do_mes(
    cartoes: Iterable[Cartao], mes: int, ano: int
) -> Iterator[tuple[CompraCartao, float]]:
    for cartao in cartoes:
        for compra in cartao.compras:
            parcela = parcela_no_mes(compra, cartao.dia_fechamento, mes, ano)
            if parcela is not None:
                yield compra, parcela[1]


def _parcelas_que_vencem_em(
    cartoes: Iterable[Cartao], mes: int, ano: int
) -> Iterator[tuple[Cartao, CompraCartao, float]]:
    for cartao in cartoes:
        f_mes, f_ano = fatura_que_vence_em(cartao, mes, ano)
        for compra, valor in _parcelas_do_mes([cartao], f_mes, f_ano):
            yield cartao, compra, valor


def gasto_cartao_por_categoria(db: Session, mes: int, ano: int) -> dict[str, float]:
    resultado: dict[str, float] = {}
    for _, compra, valor in _parcelas_que_vencem_em(db.query(Cartao).all(), mes, ano):
        resultado[compra.categoria] = round(resultado.get(compra.categoria, 0.0) + valor, 2)
    return resultado


def total_faturas_abertas(db: Session, mes: int, ano: int) -> float:
    total = 0.0
    for cartao in db.query(Cartao).all():
        f_mes, f_ano = fatura_que_vence_em(cartao, mes, ano)
        if fatura_paga(db, cartao.id, f_mes, f_ano):
            continue
        total += sum(valor for _, valor in _parcelas_do_mes([cartao], f_mes, f_ano))
    return round(total, 2)


def avisos_faturas_pagas(db: Session, compra: CompraCartao) -> list[str]:
    cartao = compra.cartao
    base_mes, base_ano = mes_referencia(compra.data_compra, cartao.dia_fechamento)
    meses = 1 if compra.recorrente else compra.parcelas
    avisos = []
    for i in range(meses):
        m, a = avancar(base_mes, base_ano, i)
        if fatura_paga(db, cartao.id, m, a):
            numero = "" if compra.recorrente else f" {i + 1}/{compra.parcelas}"
            avisos.append(
                f"A parcela{numero} caiu na fatura de {m:02d}/{a} de {cartao.nome}, "
                "que já está marcada como paga."
            )
    return avisos
