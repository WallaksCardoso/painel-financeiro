import { describe, expect, it } from "vitest";
import { formatarPercentual, formatarReal, formatarRealCurto, plural } from "./formatar";

const semEspacoEspecial = (texto: string) => texto.replace(/\s/g, " ");

describe("formatar", () => {
  it("formata reais no padrão brasileiro", () => {
    expect(semEspacoEspecial(formatarReal(1234.5))).toBe("R$ 1.234,50");
    expect(semEspacoEspecial(formatarRealCurto(1234.5))).toBe("R$ 1.235");
  });

  it("formata percentual com vírgula", () => {
    expect(formatarPercentual(28.75)).toBe("28,8%");
  });

  it("concorda singular e plural", () => {
    expect(plural(1, "compra")).toBe("1 compra");
    expect(plural(3, "item", "itens")).toBe("3 itens");
  });
});
