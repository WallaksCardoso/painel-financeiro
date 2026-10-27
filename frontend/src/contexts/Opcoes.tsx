import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { opcoesApi } from "../api";
import { useCarregar } from "../hooks/useCarregar";
import type { GrupoOpcao, Opcao } from "../types";

interface ValorOpcoes {
  lista: (grupo: GrupoOpcao) => Opcao[];
  rotulo: (grupo: GrupoOpcao, chave: string | null | undefined) => string;
  recarregar: () => void;
}

const Contexto = createContext<ValorOpcoes | null>(null);

export function OpcoesProvider({ children }: { children: ReactNode }) {
  const { dados, recarregar } = useCarregar(opcoesApi.listar, []);

  const porGrupo = useMemo(() => {
    const mapa = new Map<GrupoOpcao, Opcao[]>();
    for (const o of dados ?? []) mapa.set(o.grupo, [...(mapa.get(o.grupo) ?? []), o]);
    return mapa;
  }, [dados]);

  const lista = useCallback((grupo: GrupoOpcao) => porGrupo.get(grupo) ?? [], [porGrupo]);
  const rotulo = useCallback(
    (grupo: GrupoOpcao, chave: string | null | undefined) =>
      chave ? (porGrupo.get(grupo)?.find((o) => o.chave === chave)?.nome ?? chave) : "—",
    [porGrupo],
  );

  const valor = useMemo(() => ({ lista, rotulo, recarregar }), [lista, rotulo, recarregar]);
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useOpcoes(): ValorOpcoes {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useOpcoes precisa estar dentro de <OpcoesProvider>");
  return valor;
}
