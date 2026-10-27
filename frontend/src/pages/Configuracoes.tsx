import { Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { configApi, opcoesApi } from "../api";
import { useOpcoes } from "../contexts/Opcoes";
import { useCarregar } from "../hooks/useCarregar";
import { formatarReal } from "../lib/formatar";
import { toast } from "../toast";
import type { GrupoOpcao, Opcao } from "../types";

const GRUPOS: { grupo: GrupoOpcao; titulo: string; ajuda: string }[] = [
  {
    grupo: "categoria",
    titulo: "Categorias",
    ajuda: "Usadas em lançamentos, compras no cartão e orçamento.",
  },
  {
    grupo: "meio_pagamento",
    titulo: "Meios de pagamento",
    ajuda: "Por onde sai o dinheiro dos lançamentos (Pix, boleto…).",
  },
  {
    grupo: "origem_reserva",
    titulo: "Origens da reserva",
    ajuda: "De onde veio cada aporte na reserva de emergência.",
  },
];

export default function Configuracoes() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Configurações</h1>
        <p className="text-sm text-muted mt-1">
          Listas e valores usados no painel. Renomear não altera os lançamentos já feitos.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ConfigNumero
          chave="meta_reserva"
          rotulo="Meta da reserva de emergência (R$)"
          formatar={formatarReal}
          aviso="Meta da reserva salva."
        />
        <ConfigNumero
          chave="dias_proximas_contas"
          rotulo="Próximas contas (Dashboard): quantos dias à frente mostrar"
          inteiro
          formatar={(n) => `${n} dias`}
          aviso="Prazo das próximas contas salvo."
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {GRUPOS.map((g) => (
          <ListaEditavel key={g.grupo} {...g} />
        ))}
      </div>
    </div>
  );
}

function ConfigNumero({
  chave,
  rotulo,
  inteiro = false,
  formatar,
  aviso,
}: {
  chave: string;
  rotulo: string;
  inteiro?: boolean;
  formatar: (n: number) => string;
  aviso: string;
}) {
  const { dados, recarregar } = useCarregar(() => configApi.ler(chave), [chave]);
  const [valor, setValor] = useState<string | null>(null);
  const atual = dados !== null && dados !== undefined ? Number(dados) : null;

  async function salvar(e: FormEvent) {
    e.preventDefault();
    if (valor === null) return;
    try {
      await configApi.salvar(chave, valor);
    } catch {
      return;
    }
    toast.sucesso(aviso);
    setValor(null);
    recarregar();
  }

  return (
    <form onSubmit={salvar} className="card flex flex-wrap items-end gap-3">
      <label className="flex-1 min-w-[220px]">
        <span className="text-xs text-muted">{rotulo}</span>
        <input
          className="input w-full mt-1"
          type="number"
          step={inteiro ? 1 : 0.01}
          min={0}
          required
          value={valor ?? atual ?? ""}
          onChange={(e) => setValor(e.target.value)}
        />
      </label>
      <p className="text-sm text-muted pb-2">{atual !== null && `Atual: ${formatar(atual)}`}</p>
      <button type="submit" className="btn-primary" disabled={valor === null}>
        Salvar
      </button>
    </form>
  );
}

function ListaEditavel({ grupo, titulo, ajuda }: { grupo: GrupoOpcao; titulo: string; ajuda: string }) {
  const { lista, recarregar } = useOpcoes();
  const [novo, setNovo] = useState("");
  const [editando, setEditando] = useState<{ id: number; nome: string } | null>(null);

  async function adicionar(e: FormEvent) {
    e.preventDefault();
    if (!novo.trim()) return;
    try {
      await opcoesApi.criar(grupo, novo.trim());
    } catch {
      return;
    }
    setNovo("");
    recarregar();
  }

  async function renomear(e: FormEvent) {
    e.preventDefault();
    if (!editando || !editando.nome.trim()) return;
    try {
      await opcoesApi.atualizar(editando.id, { nome: editando.nome.trim() });
    } catch {
      return;
    }
    setEditando(null);
    recarregar();
  }

  async function apagar(o: Opcao) {
    if (!confirm(`Apagar "${o.nome}"?`)) return;
    try {
      await opcoesApi.remover(o.id);
    } catch {
      return;
    }
    recarregar();
  }

  const itens = lista(grupo);

  return (
    <div className="card p-0! overflow-hidden flex flex-col">
      <div className="p-4 border-b border-white/5">
        <h3 className="font-semibold">
          {titulo} <span className="text-muted font-normal text-sm">· {itens.length}</span>
        </h3>
        <p className="text-xs text-muted mt-0.5">{ajuda}</p>
      </div>
      <ul className="flex-1 divide-y divide-white/5 max-h-[420px] overflow-y-auto">
        {itens.map((o) => (
          <li key={o.id} className="flex items-center gap-2 px-4 py-2">
            {editando?.id === o.id ? (
              <form onSubmit={renomear} className="flex flex-1 items-center gap-1">
                <input
                  className="input flex-1 py-1!"
                  autoFocus
                  value={editando.nome}
                  onChange={(e) => setEditando({ ...editando, nome: e.target.value })}
                  onKeyDown={(e) => e.key === "Escape" && setEditando(null)}
                />
                <button type="submit" className="p-1.5 rounded-sm hover:bg-white/10" title="Salvar">
                  <Check className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  className="p-1.5 rounded-sm hover:bg-white/10"
                  onClick={() => setEditando(null)}
                  title="Cancelar"
                >
                  <X className="h-4 w-4" />
                </button>
              </form>
            ) : (
              <>
                <span className="flex-1 text-sm">{o.nome}</span>
                <button
                  className="p-1.5 rounded-sm hover:bg-white/10"
                  onClick={() => setEditando({ id: o.id, nome: o.nome })}
                  title="Renomear"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
                <button
                  className="p-1.5 rounded-sm hover:bg-danger/20 text-danger"
                  onClick={() => apagar(o)}
                  title="Apagar"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </>
            )}
          </li>
        ))}
      </ul>
      <form onSubmit={adicionar} className="flex gap-2 p-3 border-t border-white/5">
        <input
          className="input flex-1 py-1.5!"
          value={novo}
          onChange={(e) => setNovo(e.target.value)}
          placeholder="Novo item"
        />
        <button type="submit" className="btn-primary py-1.5! flex items-center gap-1" disabled={!novo.trim()}>
          <Plus className="h-4 w-4" /> Adicionar
        </button>
      </form>
    </div>
  );
}
