from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _agora() -> datetime:
    return datetime.now(UTC)


class TipoTransacao(StrEnum):
    receita = "receita"
    despesa = "despesa"
    investimento = "investimento"
    quitacao = "quitacao"
    beneficio = "beneficio"


class Situacao(StrEnum):
    nao_iniciada = "nao_iniciada"
    em_andamento = "em_andamento"
    concluido = "concluido"


class Recorrencia(StrEnum):
    mensal = "mensal"
    eventual = "eventual"
    parcelado = "parcelado"


class Prioridade(StrEnum):
    alta = "alta"
    media = "media"
    baixa = "baixa"


class TipoMovimentoReserva(StrEnum):
    aporte = "aporte"
    saque = "saque"


class Transacao(Base):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lancamento: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20), index=True)
    categoria: Mapped[str] = mapped_column(String(50), index=True)
    valor: Mapped[float] = mapped_column(Float, default=0.0)
    data: Mapped[date] = mapped_column(Date, index=True)
    meio_pagamento: Mapped[str | None] = mapped_column(String(30), nullable=True)
    situacao: Mapped[str] = mapped_column(String(20), default=Situacao.nao_iniciada.value)
    recorrencia: Mapped[str] = mapped_column(String(20), default=Recorrencia.eventual.value)
    divida_id: Mapped[int | None] = mapped_column(
        ForeignKey("dividas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parcela_atual: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parcelas_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorrente_ate: Mapped[date | None] = mapped_column(Date, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)


class Divida(Base):
    __tablename__ = "dividas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    valor_inicial: Mapped[float] = mapped_column(Float)
    total_pago: Mapped[float] = mapped_column(Float, default=0.0)
    prazo: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=Situacao.em_andamento.value)
    prioridade: Mapped[str] = mapped_column(String(20), default=Prioridade.media.value)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)


class MovimentoReserva(Base):
    __tablename__ = "movimentos_reserva"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))
    valor: Mapped[float] = mapped_column(Float)
    data: Mapped[date] = mapped_column(Date)
    origem: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)


class OrcamentoCategoria(Base):
    __tablename__ = "orcamento_categorias"
    __table_args__ = (
        UniqueConstraint("mes", "ano", "categoria", name="uq_orcamento_mes_categoria"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mes: Mapped[int] = mapped_column(Integer)
    ano: Mapped[int] = mapped_column(Integer)
    categoria: Mapped[str] = mapped_column(String(50))
    teto: Mapped[float] = mapped_column(Float, default=0.0)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)


class Cartao(Base):
    __tablename__ = "cartoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    bandeira: Mapped[str | None] = mapped_column(String(40), nullable=True)
    limite: Mapped[float] = mapped_column(Float, default=0.0)
    dia_fechamento: Mapped[int] = mapped_column(Integer, default=1)
    dia_vencimento: Mapped[int] = mapped_column(Integer, default=10)
    cor: Mapped[str] = mapped_column(String(20), default="#1b7f8f")
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)

    compras: Mapped[list["CompraCartao"]] = relationship(
        back_populates="cartao", cascade="all, delete-orphan"
    )


class CompraCartao(Base):
    __tablename__ = "compras_cartao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cartao_id: Mapped[int] = mapped_column(ForeignKey("cartoes.id", ondelete="CASCADE"), index=True)
    descricao: Mapped[str] = mapped_column(String(200))
    valor_total: Mapped[float] = mapped_column(Float)
    data_compra: Mapped[date] = mapped_column(Date, index=True)
    parcelas: Mapped[int] = mapped_column(Integer, default=1)
    categoria: Mapped[str] = mapped_column(String(50), default="geral")
    recorrente: Mapped[bool] = mapped_column(default=False)
    tags_csv: Mapped[str] = mapped_column(String(300), default="")
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)

    cartao: Mapped[Cartao] = relationship(back_populates="compras")

    @property
    def tags(self) -> list[str]:
        return [t.strip() for t in (self.tags_csv or "").split(",") if t.strip()]

    @tags.setter
    def tags(self, valor: list[str]) -> None:
        self.tags_csv = ",".join(t.strip() for t in valor if t and t.strip())


class FaturaPaga(Base):
    __tablename__ = "faturas_pagas"
    __table_args__ = (UniqueConstraint("cartao_id", "mes", "ano", name="uq_fatura_cartao_mes"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cartao_id: Mapped[int] = mapped_column(ForeignKey("cartoes.id", ondelete="CASCADE"))
    mes: Mapped[int] = mapped_column(Integer)
    ano: Mapped[int] = mapped_column(Integer)
    pago_em: Mapped[date] = mapped_column(Date)
    valor_pago: Mapped[float | None] = mapped_column(Float, nullable=True)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)


class Opcao(Base):
    __tablename__ = "opcoes"
    __table_args__ = (UniqueConstraint("grupo", "chave", name="uq_opcao_grupo_chave"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grupo: Mapped[str] = mapped_column(String(30), index=True)
    chave: Mapped[str] = mapped_column(String(50))
    nome: Mapped[str] = mapped_column(String(80))
    ordem: Mapped[int] = mapped_column(Integer, default=0)


class Configuracao(Base):
    __tablename__ = "configuracoes"

    chave: Mapped[str] = mapped_column(String(50), primary_key=True)
    valor: Mapped[str] = mapped_column(String(500))


class PlanoMes(Base):
    __tablename__ = "planos_mes"
    __table_args__ = (UniqueConstraint("mes", "ano", name="uq_plano_mes"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mes: Mapped[int] = mapped_column(Integer)
    ano: Mapped[int] = mapped_column(Integer)
    meta_descricao: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meta_valor: Mapped[float | None] = mapped_column(Float, nullable=True)
    limite_cartao: Mapped[float | None] = mapped_column(Float, nullable=True)
    anotacoes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
