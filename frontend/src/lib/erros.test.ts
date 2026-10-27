import { describe, expect, it } from "vitest";
import { mensagemDeErro } from "./erros";

describe("mensagemDeErro", () => {
  it("usa a mensagem do backend quando ela já é um texto", () => {
    expect(mensagemDeErro("Dívida não encontrada", 404)).toBe("Dívida não encontrada");
  });

  it("traduz erros de validação do Pydantic, sem repetir", () => {
    const detalhe = [
      { type: "greater_than", loc: ["body", "valor"], ctx: { gt: 0 } },
      { type: "greater_than", loc: ["body", "valor"], ctx: { gt: 0 } },
      { type: "missing", loc: ["body", "descricao"] },
    ];
    expect(mensagemDeErro(detalhe, 422)).toBe("Valor: deve ser maior que 0 · Descrição: é obrigatório");
  });

  it("cai numa frase genérica quando não há detalhe", () => {
    expect(mensagemDeErro(undefined, 500)).toBe("Erro 500 ao falar com o servidor.");
  });
});
