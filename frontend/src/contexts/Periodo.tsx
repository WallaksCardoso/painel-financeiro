import { createContext, useContext, useState, type ReactNode } from "react";
import { mesAtual } from "../lib/datas";

interface Periodo {
  mes: number;
  ano: number;
  setPeriodo: (mes: number, ano: number) => void;
}

const Contexto = createContext<Periodo | null>(null);

export function PeriodoProvider({ children }: { children: ReactNode }) {
  const [periodo, setEstado] = useState(mesAtual);
  const valor: Periodo = {
    ...periodo,
    setPeriodo: (mes, ano) => setEstado({ mes, ano }),
  };
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function usePeriodo(): Periodo {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("usePeriodo precisa estar dentro de <PeriodoProvider>");
  return valor;
}
