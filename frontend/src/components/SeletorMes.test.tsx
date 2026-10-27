import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import SeletorMes from "./SeletorMes";

describe("SeletorMes", () => {
  it("só troca o ano quando ele fica completo e válido", async () => {
    const aoMudar = vi.fn();
    render(<SeletorMes mes={10} ano={2026} aoMudar={aoMudar} />);
    const ano = screen.getByLabelText("Ano");

    await userEvent.clear(ano);
    await userEvent.type(ano, "202");
    expect(aoMudar).not.toHaveBeenCalled();

    await userEvent.type(ano, "7");
    expect(aoMudar).toHaveBeenCalledWith(10, 2027);
  });

  it("troca o mês pelo seletor", async () => {
    const aoMudar = vi.fn();
    render(<SeletorMes mes={10} ano={2026} aoMudar={aoMudar} />);
    await userEvent.selectOptions(screen.getByLabelText("Mês"), "Dezembro");
    expect(aoMudar).toHaveBeenCalledWith(12, 2026);
  });

  it("acompanha o ano quando ele muda por fora", () => {
    const { rerender } = render(<SeletorMes mes={10} ano={2026} aoMudar={() => {}} />);
    rerender(<SeletorMes mes={1} ano={2027} aoMudar={() => {}} />);
    expect(screen.getByLabelText("Ano")).toHaveValue("2027");
  });
});
