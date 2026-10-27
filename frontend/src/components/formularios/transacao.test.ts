import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { novaTransacao } from "./transacao";

describe("novaTransacao", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 27, 10, 0));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("até hoje já nasce paga", () => {
    expect(novaTransacao().situacao).toBe("concluido");
    expect(novaTransacao({ data: "2026-10-01" }).situacao).toBe("concluido");
  });

  it("com data futura nasce a pagar", () => {
    expect(novaTransacao({ data: "2026-12-10" }).situacao).toBe("nao_iniciada");
  });
});
