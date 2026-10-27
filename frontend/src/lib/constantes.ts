import type { Prioridade, Recorrencia, Situacao, TipoTransacao } from "../types";

export const LABEL_TIPO: Record<TipoTransacao, string> = {
  receita: "Receita",
  despesa: "Despesa",
  investimento: "Investimento",
  quitacao: "Quitação",
  beneficio: "Benefício",
};

export const LABEL_SITUACAO: Record<Situacao, string> = {
  nao_iniciada: "A pagar",
  em_andamento: "Em andamento",
  concluido: "Pago",
};

export function rotuloSituacao(situacao: Situacao, tipo?: string | null): string {
  if (tipo === "receita" || tipo === "beneficio") {
    if (situacao === "nao_iniciada") return "A receber";
    if (situacao === "concluido") return "Recebido";
  }
  return LABEL_SITUACAO[situacao];
}

export const LABEL_RECORRENCIA: Record<Recorrencia, string> = {
  mensal: "Mensal",
  eventual: "Eventual",
  parcelado: "Parcelado",
};

export const LABEL_PRIORIDADE: Record<Prioridade, string> = {
  alta: "Alta",
  media: "Média",
  baixa: "Baixa",
};

export const NOMES_MESES = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

export const MES_CURTO = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
