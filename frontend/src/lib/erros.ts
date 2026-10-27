interface ErroValidacao {
  type?: string;
  loc?: (string | number)[];
  msg?: string;
  ctx?: Record<string, unknown>;
}

const CAMPOS: Record<string, string> = {
  lancamento: "Lançamento",
  descricao: "Descrição",
  nome: "Nome",
  valor: "Valor",
  valor_total: "Valor",
  valor_parcela: "Valor da parcela",
  valor_inicial: "Valor da dívida",
  total_pago: "Já pago",
  valor_pago: "Valor pago",
  teto: "Teto",
  limite: "Limite",
  limite_cartao: "Limite do cartão",
  meta_valor: "Meta",
  parcelas: "Parcelas",
  parcela_atual: "Parcela atual",
  parcelas_total: "Total de parcelas",
  dia_fechamento: "Dia de fechamento",
  dia_vencimento: "Dia de vencimento",
  data: "Data",
  data_compra: "Data da compra",
  pago_em: "Data do pagamento",
  mes: "Mês",
  ano: "Ano",
  categoria: "Categoria",
  tipo: "Tipo",
  situacao: "Situação",
};

function campo(loc: ErroValidacao["loc"]): string | null {
  const ultimo = loc?.filter((p) => typeof p === "string" && !["body", "query", "path"].includes(p)).pop();
  return typeof ultimo === "string" ? (CAMPOS[ultimo] ?? ultimo) : null;
}

function traduzir(e: ErroValidacao): string {
  const nome = campo(e.loc);
  const ctx = e.ctx ?? {};
  const prefixo = nome ? `${nome}: ` : "";
  switch (e.type) {
    case "greater_than":
      return `${prefixo}deve ser maior que ${ctx.gt}`;
    case "greater_than_equal":
      return `${prefixo}deve ser no mínimo ${ctx.ge}`;
    case "less_than_equal":
      return `${prefixo}deve ser no máximo ${ctx.le}`;
    case "less_than":
      return `${prefixo}deve ser menor que ${ctx.lt}`;
    case "string_too_short":
    case "missing":
      return `${prefixo}é obrigatório`;
    case "string_too_long":
      return `${prefixo}texto longo demais (máximo ${ctx.max_length})`;
    case "date_from_datetime_parsing":
    case "date_parsing":
    case "date_type":
      return `${prefixo}data inválida`;
    case "int_parsing":
    case "float_parsing":
    case "int_type":
    case "float_type":
      return `${prefixo}informe um número`;
    case "literal_error":
    case "enum":
      return `${prefixo}opção inválida`;
    case "value_error":
      return (e.msg ?? "").replace(/^Value error,\s*/i, "");
    default:
      return `${prefixo}${e.msg ?? "valor inválido"}`;
  }
}

export function mensagemDeErro(detalhe: unknown, status?: number): string {
  if (typeof detalhe === "string") return detalhe;
  if (Array.isArray(detalhe) && detalhe.length > 0) {
    const frases = [...new Set(detalhe.map((e) => traduzir(e as ErroValidacao)))];
    const texto = frases.join(" · ");
    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }
  return status ? `Erro ${status} ao falar com o servidor.` : "Algo deu errado.";
}
