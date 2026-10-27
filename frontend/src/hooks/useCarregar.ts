import { useCallback, useEffect, useLayoutEffect, useRef, useState, type DependencyList } from "react";

interface Carregamento<T> {
  dados: T | null;
  carregando: boolean;
  erro: boolean;
  recarregar: () => void;
}

export function useCarregar<T>(buscar: () => Promise<T>, deps: DependencyList): Carregamento<T> {
  const [dados, setDados] = useState<T | null>(null);
  const [erro, setErro] = useState(false);
  const [versao, setVersao] = useState(0);

  const buscarAtual = useRef(buscar);
  useLayoutEffect(() => {
    buscarAtual.current = buscar;
  });

  useEffect(() => {
    let ativo = true;
    buscarAtual
      .current()
      .then((r) => {
        if (!ativo) return;
        setDados(r);
        setErro(false);
      })
      .catch(() => {
        if (ativo) setErro(true);
      });
    return () => {
      ativo = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, versao]);

  const recarregar = useCallback(() => setVersao((v) => v + 1), []);

  return { dados, carregando: dados === null && !erro, erro, recarregar };
}
