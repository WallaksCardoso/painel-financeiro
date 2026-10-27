import { afterEach, describe, expect, it, vi } from "vitest";
import { dataPadrao, hojeISO } from "./datas";

describe("datas", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("hoje usa o fuso local, não UTC (à noite no Brasil o UTC já é amanhã)", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 27, 23, 30));
    expect(hojeISO()).toBe("2026-10-27");
  });

  it("data padrão é hoje no mês atual e dia 1 nos outros meses", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 27, 10, 0));
    expect(dataPadrao(10, 2026)).toBe("2026-10-27");
    expect(dataPadrao(12, 2026)).toBe("2026-12-01");
  });
});
