import { describe, expect, it } from "vitest";
import { rotuloSituacao } from "./constantes";

describe("rotuloSituacao", () => {
  it("entradas são recebidas, saídas são pagas", () => {
    expect(rotuloSituacao("nao_iniciada", "receita")).toBe("A receber");
    expect(rotuloSituacao("concluido", "beneficio")).toBe("Recebido");
    expect(rotuloSituacao("nao_iniciada", "despesa")).toBe("A pagar");
    expect(rotuloSituacao("concluido", "despesa")).toBe("Pago");
  });
});
