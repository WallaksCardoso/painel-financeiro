from datetime import date, datetime
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


def texto(maximo: int):
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=maximo)]


TipoTransacao = Literal["receita", "despesa", "investimento", "quitacao", "beneficio"]
Situacao = Literal["nao_iniciada", "em_andamento", "concluido"]
Recorrencia = Literal["mensal", "eventual", "parcelado"]
Prioridade = Literal["alta", "media", "baixa"]
TipoMovimentoReserva = Literal["aporte", "saque"]


class Atualizacao(BaseModel):
    anulaveis: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _sem_nulo_em_obrigatorio(self):
        for campo in self.model_fields_set:
            if getattr(self, campo) is None and campo not in self.anulaveis:
                raise ValueError(f"o campo '{campo}' não pode ser nulo")
        return self


class TransacaoBase(BaseModel):
    lancamento: texto(200)
    tipo: TipoTransacao
    categoria: texto(50)
    valor: float = Field(default=0.0, ge=0)
    data: date
    meio_pagamento: str | None = None
    situacao: Situacao = "nao_iniciada"
    recorrencia: Recorrencia = "eventual"
    divida_id: int | None = None
    observacao: str | None = None
    parcela_atual: int | None = Field(None, ge=1, le=360)
    parcelas_total: int | None = Field(None, ge=1, le=360)

    @model_validator(mode="after")
    def _parcela_coerente(self):
        validar_parcela(self.parcela_atual, self.parcelas_total)
        return self


def validar_parcela(atual: int | None, total: int | None) -> None:
    if (atual is None) != (total is None):
        raise ValueError("informe a parcela atual e o total de parcelas juntos")
    if atual is not None and total is not None and atual > total:
        raise ValueError("a parcela atual não pode ser maior que o total de parcelas")


class TransacaoCreate(TransacaoBase):
    pass


class TransacaoUpdate(Atualizacao):
    anulaveis = frozenset(
        {"meio_pagamento", "divida_id", "observacao", "parcela_atual", "parcelas_total"}
    )

    lancamento: texto(200) | None = None
    tipo: TipoTransacao | None = None
    categoria: texto(50) | None = None
    valor: float | None = Field(None, ge=0)
    data: date | None = None
    meio_pagamento: str | None = None
    situacao: Situacao | None = None
    recorrencia: Recorrencia | None = None
    divida_id: int | None = None
    observacao: str | None = None
    parcela_atual: int | None = Field(None, ge=1, le=360)
    parcelas_total: int | None = Field(None, ge=1, le=360)


class EncerrarRecorrencia(BaseModel):
    lancamento: str
    categoria: str
    mes: int = Field(ge=1, le=12)
    ano: int = Field(ge=2000, le=2100)


class TransacaoOut(TransacaoBase):
    id: int
    recorrente_ate: date | None = None
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class DividaBase(BaseModel):
    nome: texto(120)
    valor_inicial: float = Field(gt=0)
    total_pago: float = Field(default=0.0, ge=0)
    prazo: date | None = None
    status: Situacao = "em_andamento"
    prioridade: Prioridade = "media"
    observacao: str | None = None


class DividaCreate(DividaBase):
    @model_validator(mode="after")
    def _pago_ate_o_valor(self):
        if self.total_pago > self.valor_inicial:
            raise ValueError("o valor já pago não pode ser maior que o valor da dívida")
        return self


class DividaUpdate(Atualizacao):
    anulaveis = frozenset({"prazo", "observacao"})

    nome: texto(120) | None = None
    valor_inicial: float | None = Field(None, gt=0)
    total_pago: float | None = Field(None, ge=0)
    prazo: date | None = None
    status: Situacao | None = None
    prioridade: Prioridade | None = None
    observacao: str | None = None


class DividaOut(DividaBase):
    id: int
    criado_em: datetime
    pago_vinculado: float
    pago_efetivo: float
    restante: float
    progresso: float
    model_config = ConfigDict(from_attributes=True)


class MovimentoReservaBase(BaseModel):
    descricao: texto(200)
    tipo: TipoMovimentoReserva
    valor: float = Field(gt=0)
    data: date
    origem: str | None = None
    observacao: str | None = None


class MovimentoReservaCreate(MovimentoReservaBase):
    pass


class MovimentoReservaUpdate(Atualizacao):
    anulaveis = frozenset({"origem", "observacao"})

    descricao: texto(200) | None = None
    tipo: TipoMovimentoReserva | None = None
    valor: float | None = Field(None, gt=0)
    data: date | None = None
    origem: str | None = None
    observacao: str | None = None


class MovimentoReservaOut(MovimentoReservaBase):
    id: int
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class ReservaSaldo(BaseModel):
    saldo: float
    total_aportes: float
    total_saques: float
    quantidade_movimentos: int


class OrcamentoBase(BaseModel):
    mes: int = Field(ge=1, le=12)
    ano: int = Field(ge=2000, le=2100)
    categoria: texto(50)
    teto: float = Field(ge=0)


class OrcamentoCreate(OrcamentoBase):
    pass


class OrcamentoUpdate(Atualizacao):
    teto: float | None = Field(None, ge=0)
    categoria: texto(50) | None = None
    mes: int | None = Field(None, ge=1, le=12)
    ano: int | None = Field(None, ge=2000, le=2100)


class OrcamentoOut(OrcamentoBase):
    id: int
    gasto: float
    restante: float
    uso_percentual: float
    status: str
    model_config = ConfigDict(from_attributes=True)


class CartaoBase(BaseModel):
    nome: texto(80)
    bandeira: str | None = None
    limite: float = Field(default=0.0, ge=0)
    dia_fechamento: int = Field(default=1, ge=1, le=31)
    dia_vencimento: int = Field(default=10, ge=1, le=31)
    cor: str = "#1b7f8f"
    ativo: bool = True


class CartaoCreate(CartaoBase):
    pass


class CartaoUpdate(Atualizacao):
    anulaveis = frozenset({"bandeira"})

    nome: texto(80) | None = None
    bandeira: str | None = None
    limite: float | None = Field(None, ge=0)
    dia_fechamento: int | None = Field(None, ge=1, le=31)
    dia_vencimento: int | None = Field(None, ge=1, le=31)
    cor: str | None = None
    ativo: bool | None = None


class CartaoOut(CartaoBase):
    id: int
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class CompraCartaoBase(BaseModel):
    cartao_id: int
    descricao: texto(200)
    valor_total: float = Field(ge=0)
    data_compra: date
    parcelas: int = Field(default=1, ge=1, le=60)
    categoria: texto(50) = "geral"
    recorrente: bool = False
    tags: list[str] = Field(default_factory=list)
    observacao: str | None = None


class CompraCartaoCreate(CompraCartaoBase):
    @model_validator(mode="after")
    def _regras_de_compra(self):
        validar_compra(self.recorrente, self.valor_total, self.parcelas)
        return self


def validar_compra(recorrente: bool, valor_total: float, parcelas: int) -> None:
    if not recorrente and valor_total <= 0:
        raise ValueError("o valor deve ser maior que zero (só assinaturas podem ficar sem valor)")
    if recorrente and parcelas != 1:
        raise ValueError("assinatura (despesa fixa do cartão) não tem parcelas: use 1")


class CompraEmAndamentoCreate(BaseModel):
    cartao_id: int
    descricao: texto(200)
    valor_parcela: float = Field(gt=0)
    parcela_atual: int = Field(ge=1, le=60)
    parcelas_total: int = Field(ge=1, le=60)
    mes: int = Field(ge=1, le=12)
    ano: int = Field(ge=2000, le=2100)
    vence_em: bool = False
    categoria: texto(50) = "geral"
    tags: list[str] = Field(default_factory=list)
    observacao: str | None = None

    @model_validator(mode="after")
    def _atual_ate_o_total(self):
        if self.parcela_atual > self.parcelas_total:
            raise ValueError("parcela_atual não pode ser maior que parcelas_total")
        return self


class CompraCartaoUpdate(Atualizacao):
    anulaveis = frozenset({"observacao"})

    cartao_id: int | None = None
    descricao: texto(200) | None = None
    valor_total: float | None = Field(None, ge=0)
    data_compra: date | None = None
    parcelas: int | None = Field(None, ge=1, le=60)
    categoria: texto(50) | None = None
    recorrente: bool | None = None
    tags: list[str] | None = None
    observacao: str | None = None


class CompraCartaoOut(CompraCartaoBase):
    id: int
    criado_em: datetime
    valor_parcela: float
    primeira_fatura_mes: int
    primeira_fatura_ano: int
    avisos: list[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class ItemFatura(BaseModel):
    compra_id: int
    descricao: str
    categoria: str
    parcela_atual: int
    parcelas_total: int
    parcelas_restantes: int
    valor_parcela: float
    data_compra: date
    recorrente: bool
    tags: list[str]


class FaturaMes(BaseModel):
    cartao_id: int
    cartao_nome: str
    mes: int
    ano: int
    vencimento: date
    total: float
    total_fixo: float
    total_variavel: float
    total_comprometido_futuro: float
    itens: list[ItemFatura]
    pago: bool = False
    fatura_paga_id: int | None = None
    pago_em: date | None = None
    valor_pago: float | None = None


class FaturaPagaCreate(BaseModel):
    mes: int = Field(ge=1, le=12)
    ano: int = Field(ge=2000, le=2100)
    pago_em: date | None = None
    valor_pago: float | None = Field(None, ge=0)
    observacao: str | None = None


class FaturaPagaOut(BaseModel):
    id: int
    cartao_id: int
    mes: int
    ano: int
    pago_em: date
    valor_pago: float | None
    observacao: str | None
    model_config = ConfigDict(from_attributes=True)


class ResumoMes(BaseModel):
    mes: int
    ano: int
    entradas: float
    saidas: float
    saldo: float
    quitacoes: float
    investimentos: float
    cartao: float


class CategoriaTotal(BaseModel):
    categoria: str
    total: float


class ProximaConta(BaseModel):
    id: str
    lancamento: str
    valor: float
    data: date
    dias_ate_vencer: int
    categoria: str | None


class DashboardCompleto(BaseModel):
    resumo: ResumoMes
    por_categoria: list[CategoriaTotal]
    saldo_reserva: float
    total_dividas_restante: float
    fatura_aberta: float
    proximas_contas: list[ProximaConta]


class LinhaProjecao(BaseModel):
    descricao: str
    grupo: Literal["entrada", "conta", "quitacao", "investimento", "cartao", "beneficio"]
    valor: float
    dia: int | None
    previsto: bool


class ParcelaTerminando(BaseModel):
    compra_id: int
    descricao: str
    cartao_nome: str
    valor_parcela: float


class ParcelaAtiva(BaseModel):
    compra_id: int
    descricao: str
    cartao_nome: str
    parcela_atual: int
    parcelas_total: int
    valor_parcela: float
    comeca_mes: int
    comeca_ano: int
    termina_mes: int
    termina_ano: int


class ProjecaoMes(BaseModel):
    mes: int
    ano: int
    entradas: float
    contas: float
    quitacoes: float
    investimentos: float
    cartao: float
    saidas: float
    sobra: float
    acumulado: float
    linhas: list[LinhaProjecao]
    terminando: list[ParcelaTerminando]


class Projecao(BaseModel):
    meses: list[ProjecaoMes]
    parcelas_ativas: list[ParcelaAtiva]
    sem_valor: list[str]


GrupoOpcao = Literal["categoria", "meio_pagamento", "origem_reserva"]


class OpcaoCreate(BaseModel):
    grupo: GrupoOpcao
    nome: texto(80)


class OpcaoUpdate(Atualizacao):
    nome: texto(80) | None = None
    ordem: int | None = Field(None, ge=0)


class OpcaoOut(BaseModel):
    id: int
    grupo: GrupoOpcao
    chave: str
    nome: str
    ordem: int
    model_config = ConfigDict(from_attributes=True)


class ConfiguracaoIn(BaseModel):
    valor: str = Field(max_length=500)


class ConfiguracaoOut(BaseModel):
    chave: str
    valor: str | None


class PlanoMesIn(BaseModel):
    meta_descricao: str | None = Field(None, max_length=200)
    meta_valor: float | None = Field(None, ge=0)
    limite_cartao: float | None = Field(None, ge=0)
    anotacoes: str | None = Field(None, max_length=4000)


class PlanoMesOut(PlanoMesIn):
    mes: int
    ano: int
    salvo: bool


class ItemMes(BaseModel):
    origem: Literal["transacao", "compra", "previsto"]
    tipo: Literal["receita", "despesa", "investimento", "quitacao", "beneficio", "cartao"]
    id: int | None
    molde_id: int | None = None
    recorrencia: str | None = None
    descricao: str
    valor: float | None
    dia: int | None
    quantidade: str
    meio: str | None
    situacao: str | None
    categoria: str
    observacao: str | None


class ResumoMesPlano(BaseModel):
    mes: int
    ano: int
    plano: PlanoMesOut
    receitas: list[ItemMes]
    beneficios: list[ItemMes]
    fixos: list[ItemMes]
    outras: list[ItemMes]
    dividas: list[ItemMes]
    total_receitas: float
    total_beneficios: float
    fixo_conta: float
    fixo_cartao: float
    gasto_fixo: float
    total_dividas: float
    outras_despesas: float
    cartao_variavel: float
    primeira_entrada: ItemMes | None
    sobra_primeira_entrada: float | None
    livre: float
    previstos: int
