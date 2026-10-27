import { hojeISO } from "../../lib/datas";
import type { Transacao, TransacaoInput } from "../../types";

export function novaTransacao(parcial: Partial<TransacaoInput> = {}): TransacaoInput {
  const data = parcial.data ?? hojeISO();
  return {
    lancamento: "",
    tipo: "despesa",
    categoria: "geral",
    valor: 0,
    data,
    meio_pagamento: "pix",
    situacao: data > hojeISO() ? "nao_iniciada" : "concluido",
    recorrencia: "eventual",
    divida_id: null,
    observacao: null,
    parcela_atual: null,
    parcelas_total: null,
    ...parcial,
  };
}

export function transacaoParaInput(t: Transacao): TransacaoInput {
  return {
    lancamento: t.lancamento,
    tipo: t.tipo,
    categoria: t.categoria,
    valor: t.valor,
    data: t.data,
    meio_pagamento: t.meio_pagamento,
    situacao: t.situacao,
    recorrencia: t.recorrencia,
    divida_id: t.divida_id,
    observacao: t.observacao,
    parcela_atual: t.parcela_atual,
    parcelas_total: t.parcelas_total,
  };
}
