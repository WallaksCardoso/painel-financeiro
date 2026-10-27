export type TipoTransacao = "receita" | "despesa" | "investimento" | "quitacao" | "beneficio";
export type Situacao = "nao_iniciada" | "em_andamento" | "concluido";
export type Recorrencia = "mensal" | "eventual" | "parcelado";
export type Prioridade = "alta" | "media" | "baixa";

export interface Transacao {
  id: number;
  lancamento: string;
  tipo: TipoTransacao;
  categoria: string;
  valor: number;
  data: string;
  meio_pagamento: string | null;
  situacao: Situacao;
  recorrencia: Recorrencia;
  divida_id: number | null;
  observacao: string | null;
  parcela_atual: number | null;
  parcelas_total: number | null;
  recorrente_ate: string | null;
  criado_em: string;
}
export type TransacaoInput = Omit<Transacao, "id" | "criado_em" | "recorrente_ate">;

export interface Divida {
  id: number;
  nome: string;
  valor_inicial: number;
  total_pago: number;
  prazo: string | null;
  status: Situacao;
  prioridade: Prioridade;
  observacao: string | null;
  criado_em: string;
  pago_vinculado: number;
  pago_efetivo: number;
  restante: number;
  progresso: number;
}
export type DividaInput = Omit<
  Divida,
  "id" | "criado_em" | "restante" | "progresso" | "pago_vinculado" | "pago_efetivo"
>;

export interface MovimentoReserva {
  id: number;
  descricao: string;
  tipo: "aporte" | "saque";
  valor: number;
  data: string;
  origem: string | null;
  observacao: string | null;
  criado_em: string;
}
export type MovimentoReservaInput = Omit<MovimentoReserva, "id" | "criado_em">;

export interface ReservaSaldo {
  saldo: number;
  total_aportes: number;
  total_saques: number;
  quantidade_movimentos: number;
}

export interface OrcamentoCategoria {
  id: number;
  mes: number;
  ano: number;
  categoria: string;
  teto: number;
  gasto: number;
  restante: number;
  uso_percentual: number;
  status: "ok" | "atencao" | "estourou";
}
export type OrcamentoInput = Pick<OrcamentoCategoria, "mes" | "ano" | "categoria" | "teto">;

export interface Cartao {
  id: number;
  nome: string;
  bandeira: string | null;
  limite: number;
  dia_fechamento: number;
  dia_vencimento: number;
  cor: string;
  ativo: boolean;
  criado_em: string;
}
export type CartaoInput = Omit<Cartao, "id" | "criado_em">;

export interface CompraCartao {
  id: number;
  cartao_id: number;
  descricao: string;
  valor_total: number;
  data_compra: string;
  parcelas: number;
  categoria: string;
  recorrente: boolean;
  tags: string[];
  observacao: string | null;
  criado_em: string;
  valor_parcela: number;
  primeira_fatura_mes: number;
  primeira_fatura_ano: number;
  avisos: string[];
}
export type CompraCartaoInput = Omit<
  CompraCartao,
  "id" | "criado_em" | "valor_parcela" | "primeira_fatura_mes" | "primeira_fatura_ano" | "avisos"
>;

export interface ItemFatura {
  compra_id: number;
  descricao: string;
  categoria: string;
  parcela_atual: number;
  parcelas_total: number;
  parcelas_restantes: number;
  valor_parcela: number;
  data_compra: string;
  recorrente: boolean;
  tags: string[];
}

export interface FaturaMes {
  cartao_id: number;
  cartao_nome: string;
  mes: number;
  ano: number;
  vencimento: string;
  total: number;
  total_fixo: number;
  total_variavel: number;
  total_comprometido_futuro: number;
  itens: ItemFatura[];
  pago: boolean;
  fatura_paga_id: number | null;
  pago_em: string | null;
  valor_pago: number | null;
}

export interface FaturaPagaInput {
  mes: number;
  ano: number;
  pago_em?: string | null;
  valor_pago?: number | null;
  observacao?: string | null;
}

export interface FaturaPaga {
  id: number;
  cartao_id: number;
  mes: number;
  ano: number;
  pago_em: string;
  valor_pago: number | null;
  observacao: string | null;
}

export interface ResumoMes {
  mes: number;
  ano: number;
  entradas: number;
  saidas: number;
  saldo: number;
  quitacoes: number;
  investimentos: number;
  cartao: number;
}

export interface CategoriaTotal {
  categoria: string;
  total: number;
}

export interface ProximaConta {
  id: string;
  lancamento: string;
  valor: number;
  data: string;
  dias_ate_vencer: number;
  categoria: string | null;
}

export interface DashboardCompleto {
  resumo: ResumoMes;
  por_categoria: CategoriaTotal[];
  saldo_reserva: number;
  total_dividas_restante: number;
  fatura_aberta: number;
  proximas_contas: ProximaConta[];
}

export interface CompraEmAndamentoInput {
  cartao_id: number;
  descricao: string;
  valor_parcela: number;
  parcela_atual: number;
  parcelas_total: number;
  mes: number;
  ano: number;
  vence_em?: boolean;
  categoria: string;
  tags: string[];
  observacao: string | null;
}

export type GrupoProjecao = "entrada" | "conta" | "quitacao" | "investimento" | "cartao" | "beneficio";

export interface LinhaProjecao {
  descricao: string;
  grupo: GrupoProjecao;
  valor: number;
  dia: number | null;
  previsto: boolean;
}

export interface ParcelaTerminando {
  compra_id: number;
  descricao: string;
  cartao_nome: string;
  valor_parcela: number;
}

export interface ParcelaAtiva {
  compra_id: number;
  descricao: string;
  cartao_nome: string;
  parcela_atual: number;
  parcelas_total: number;
  valor_parcela: number;
  comeca_mes: number;
  comeca_ano: number;
  termina_mes: number;
  termina_ano: number;
}

export interface ProjecaoMes {
  mes: number;
  ano: number;
  entradas: number;
  contas: number;
  quitacoes: number;
  investimentos: number;
  cartao: number;
  saidas: number;
  sobra: number;
  acumulado: number;
  linhas: LinhaProjecao[];
  terminando: ParcelaTerminando[];
}

export interface Projecao {
  meses: ProjecaoMes[];
  parcelas_ativas: ParcelaAtiva[];
  sem_valor: string[];
}

export type GrupoOpcao = "categoria" | "meio_pagamento" | "origem_reserva";

export interface Opcao {
  id: number;
  grupo: GrupoOpcao;
  chave: string;
  nome: string;
  ordem: number;
}

export interface PlanoMesInput {
  meta_descricao: string | null;
  meta_valor: number | null;
  limite_cartao: number | null;
  anotacoes: string | null;
}

export interface PlanoMes extends PlanoMesInput {
  mes: number;
  ano: number;
  salvo: boolean;
}

export interface ItemMes {
  origem: "transacao" | "compra" | "previsto";
  tipo: TipoTransacao | "cartao";
  id: number | null;
  molde_id: number | null;
  recorrencia: Recorrencia | null;
  descricao: string;
  valor: number | null;
  dia: number | null;
  quantidade: string;
  meio: string | null;
  situacao: Situacao | null;
  categoria: string;
  observacao: string | null;
}

export interface ResumoMesPlano {
  mes: number;
  ano: number;
  plano: PlanoMes;
  receitas: ItemMes[];
  beneficios: ItemMes[];
  fixos: ItemMes[];
  outras: ItemMes[];
  dividas: ItemMes[];
  total_receitas: number;
  total_beneficios: number;
  fixo_conta: number;
  fixo_cartao: number;
  gasto_fixo: number;
  outras_despesas: number;
  total_dividas: number;
  cartao_variavel: number;
  primeira_entrada: ItemMes | null;
  sobra_primeira_entrada: number | null;
  livre: number;
  previstos: number;
}
