import re
import unicodedata

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import (
    CompraCartao,
    Configuracao,
    MovimentoReserva,
    Opcao,
    OrcamentoCategoria,
    Transacao,
)

PADROES: dict[str, list[tuple[str, str]]] = {
    "categoria": [
        ("salario", "Salário"),
        ("renda_extra", "Renda extra"),
        ("comida", "Alimentação"),
        ("apartamento", "Moradia"),
        ("casa_roca", "Casa na roça"),
        ("carro", "Carro"),
        ("gasolina", "Combustível"),
        ("internet", "Internet"),
        ("saude", "Saúde"),
        ("lazer", "Lazer"),
        ("roupas", "Roupas"),
        ("assinaturas", "Assinaturas"),
        ("crescimento", "Crescimento"),
        ("utilidade", "Serviços"),
        ("quitacao", "Quitação"),
        ("reserva", "Reserva"),
        ("geral", "Geral"),
    ],
    "meio_pagamento": [
        ("pix", "Pix"),
        ("dinheiro", "Dinheiro"),
        ("debito", "Débito"),
        ("credito", "Crédito"),
        ("boleto", "Boleto"),
        ("transferencia", "Transferência"),
        ("debito_automatico", "Débito automático"),
    ],
    "origem_reserva": [
        ("salario", "Salário"),
        ("renda_extra", "Renda extra"),
        ("emergencia", "Emergência"),
        ("outro", "Outro"),
    ],
}


CONFIGURACOES: dict[str, tuple[float, float, bool]] = {
    "meta_reserva": (0, 100_000_000, False),
    "dias_proximas_contas": (1, 90, True),
}

CONFIGURACOES_INICIAIS = {"meta_reserva": "8000", "dias_proximas_contas": "15"}


def gerar_chave(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")[:50] or "opcao"


def nome_repetido(
    db: Session, grupo: str, nome: str, ignorar_id: int | None = None
) -> Opcao | None:
    alvo = gerar_chave(nome)
    for o in db.query(Opcao).filter(Opcao.grupo == grupo):
        if o.id != ignorar_id and gerar_chave(o.nome) == alvo:
            return o
    return None


def chave_livre(db: Session, grupo: str, nome: str) -> str:
    base = gerar_chave(nome)
    chave, n = base, 2
    while db.query(Opcao).filter(Opcao.grupo == grupo, Opcao.chave == chave).first():
        chave, n = f"{base}_{n}", n + 1
    return chave


def _em_uso_por_grupo(db: Session) -> dict[str, set[str]]:

    def distintos(coluna) -> set[str]:
        return {v for (v,) in db.query(coluna).distinct() if v}

    return {
        "categoria": distintos(Transacao.categoria)
        | distintos(CompraCartao.categoria)
        | distintos(OrcamentoCategoria.categoria),
        "meio_pagamento": distintos(Transacao.meio_pagamento),
        "origem_reserva": distintos(MovimentoReserva.origem),
    }


def usos(db: Session, opcao: Opcao) -> int:

    def contar(coluna) -> int:
        return db.query(func.count()).filter(coluna == opcao.chave).scalar() or 0

    if opcao.grupo == "categoria":
        return (
            contar(Transacao.categoria)
            + contar(CompraCartao.categoria)
            + contar(OrcamentoCategoria.categoria)
        )
    if opcao.grupo == "meio_pagamento":
        return contar(Transacao.meio_pagamento)
    return contar(MovimentoReserva.origem)


def semear(db: Session) -> None:
    em_uso = _em_uso_por_grupo(db)
    for grupo, padroes in PADROES.items():
        existentes = {o.chave for o in db.query(Opcao).filter(Opcao.grupo == grupo)}
        novos: list[tuple[str, str]] = []
        if not existentes:
            novos += padroes
        conhecidas = existentes | {chave for chave, _ in novos}
        novos += [(c, c.replace("_", " ").capitalize()) for c in sorted(em_uso[grupo] - conhecidas)]
        ordem = len(existentes)
        for chave, nome in novos:
            db.add(Opcao(grupo=grupo, chave=chave, nome=nome, ordem=ordem))
            ordem += 1
    for chave, valor in CONFIGURACOES_INICIAIS.items():
        if db.get(Configuracao, chave) is None:
            db.add(Configuracao(chave=chave, valor=valor))
    db.commit()
