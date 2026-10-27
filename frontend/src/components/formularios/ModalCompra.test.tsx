import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Cartao } from "../../types";
import ModalCompra from "./ModalCompra";

vi.mock("../../contexts/Opcoes", () => ({
  useOpcoes: () => ({
    lista: () => [{ id: 1, grupo: "categoria", chave: "geral", nome: "Geral", ordem: 0 }],
    rotulo: (_grupo: string, chave: string) => chave,
    recarregar: () => {},
  }),
}));

const cartao = { id: 1, nome: "Cartão X", dia_fechamento: 8, dia_vencimento: 15 } as Cartao;

function abrir() {
  render(
    <ModalCompra
      cartoes={[cartao]}
      cartaoId={1}
      mes={10}
      ano={2026}
      editando={null}
      aoFechar={() => {}}
      aoSalvar={() => {}}
    />,
  );
}

describe("ModalCompra", () => {
  it("mostra o valor das parcelas com os centavos na última", async () => {
    abrir();
    await userEvent.type(screen.getByLabelText("Valor total (R$)"), "100");
    const parcelas = screen.getByLabelText("Parcelas");
    await userEvent.clear(parcelas);
    await userEvent.type(parcelas, "3");

    expect(screen.getByText(/3× de/)).toHaveTextContent(/R\$\s33,33.*a última de R\$\s33,34/);
  });

  it("assinatura esconde as parcelas e, ao desmarcar, devolve o número anterior", async () => {
    abrir();
    const parcelas = screen.getByLabelText("Parcelas");
    await userEvent.clear(parcelas);
    await userEvent.type(parcelas, "4");

    const assinatura = screen.getByRole("checkbox");
    await userEvent.click(assinatura);
    expect(screen.queryByLabelText("Parcelas")).not.toBeInTheDocument();

    await userEvent.click(assinatura);
    expect(screen.getByLabelText("Parcelas")).toHaveValue(4);
  });
});
