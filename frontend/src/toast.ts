import { useSyncExternalStore } from "react";

export type TipoToast = "erro" | "sucesso" | "info";

export interface Toast {
  id: number;
  tipo: TipoToast;
  mensagem: string;
}

let toasts: Toast[] = [];
const ouvintes = new Set<() => void>();
let seq = 0;

function emitir() {
  ouvintes.forEach((o) => o());
}

export function pushToast(mensagem: string, tipo: TipoToast = "info") {
  const id = ++seq;
  toasts = [...toasts, { id, tipo, mensagem }];
  emitir();
  setTimeout(() => removerToast(id), 5000);
}

export function removerToast(id: number) {
  toasts = toasts.filter((t) => t.id !== id);
  emitir();
}

export const toast = {
  erro: (m: string) => pushToast(m, "erro"),
  sucesso: (m: string) => pushToast(m, "sucesso"),
  info: (m: string) => pushToast(m, "info"),
};

export function useToasts(): Toast[] {
  return useSyncExternalStore(
    (cb) => {
      ouvintes.add(cb);
      return () => ouvintes.delete(cb);
    },
    () => toasts,
    () => toasts,
  );
}
