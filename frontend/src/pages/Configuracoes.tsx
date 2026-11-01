import { Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { configApi, metasApi, opcoesApi } from "../api";
import { useOpcoes } from "../contexts/Opcoes";
import { useCarregar } from "../hooks/useCarregar";
import { NOMES_MESES } from "../lib/constantes";
import { formatarReal } from "../lib/formatar";
import { toast } from "../toast";
import type { GrupoOpcao, MetaPoupanca, MetaPoupancaInput, Opcao } from "../types";

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

      <MetasPoupanca />

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

function proximoMes(): { mes: number; ano: number } {
  const hoje = new Date();
  const mes = hoje.getMonth() + 2;
  return mes > 12 ? { mes: 1, ano: hoje.getFullYear() + 1 } : { mes, ano: hoje.getFullYear() };
}

function metaVazia(): MetaPoupancaInput {
  return { valor: 0, orcamento_variavel: null, ...proximoMes() };
}

function MetasPoupanca() {
  const { dados: metas, recarregar } = useCarregar(() => metasApi.listar(), []);
  const [form, setForm] = useState<MetaPoupancaInput>(metaVazia);
  const [editandoId, setEditandoId] = useState<number | null>(null);

  function editar(m: MetaPoupanca) {
    setEditandoId(m.id);
    setForm({ valor: m.valor, orcamento_variavel: m.orcamento_variavel, mes: m.mes, ano: m.ano });
  }

  function cancelar() {
    setEditandoId(null);
    setForm(metaVazia());
  }

  async function salvar(e: FormEvent) {
    e.preventDefault();
    try {
      if (editandoId === null) await metasApi.criar(form);
      else await metasApi.atualizar(editandoId, form);
    } catch {
      return;
    }
    toast.sucesso("Meta de poupança salva.");
    cancelar();
    recarregar();
  }

  async function remover(m: MetaPoupanca) {
    try {
      await metasApi.remover(m.id);
    } catch {
      return;
    }
    toast.sucesso("Meta removida.");
    if (editandoId === m.id) cancelar();
    recarregar();
  }

  return (
    <div className="card space-y-4">
      <div>
        <h3 className="font-semibold">Meta de poupança</h3>
        <p className="text-xs text-muted mt-0.5">
          Quanto guardar por mês a partir de um mês. Vale para todos os meses seguintes até a próxima meta;
          para mudar um mês só, use o "Plano do mês". O orçamento do variável é a estimativa de gastos do dia
          a dia usada no Fluxo de caixa.
        </p>
      </div>

      {metas && metas.length > 0 && (
        <ul className="divide-y divide-white/5">
          {metas.map((m) => (
            <li key={m.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-2">
              <p className="flex-1 min-w-[200px]">
                A partir de {NOMES_MESES[m.mes - 1].toLowerCase()} de {m.ano}: guardar{" "}
                <span className="font-semibold">{formatarReal(m.valor)}</span>
                {m.orcamento_variavel !== null && (
                  <span className="text-muted"> · variável {formatarReal(m.orcamento_variavel)}</span>
                )}
              </p>
              <button type="button" className="btn-ghost p-1.5!" title="Editar" onClick={() => editar(m)}>
                <Pencil className="h-4 w-4" />
              </button>
              <button
                type="button"
                className="btn-ghost p-1.5! text-danger"
                title="Apagar"
                onClick={() => remover(m)}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={salvar} className="flex flex-wrap items-end gap-3">
        <label>
          <span className="text-xs text-muted">Guardar por mês (R$)</span>
          <input
            className="input w-36 mt-1"
            type="number"
            step={0.01}
            min={0}
            required
            value={form.valor || ""}
            onChange={(e) => setForm({ ...form, valor: Number(e.target.value) })}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Orçamento do variável (R$, opcional)</span>
          <input
            className="input w-36 mt-1"
            type="number"
            step={0.01}
            min={0}
            value={form.orcamento_variavel ?? ""}
            onChange={(e) =>
              setForm({ ...form, orcamento_variavel: e.target.value === "" ? null : Number(e.target.value) })
            }
          />
        </label>
        <label>
          <span className="text-xs text-muted">A partir de</span>
          <div className="flex gap-2 mt-1">
            <select
              className="input"
              value={form.mes}
              onChange={(e) => setForm({ ...form, mes: Number(e.target.value) })}
            >
              {NOMES_MESES.map((nome, i) => (
                <option key={nome} value={i + 1}>
                  {nome}
                </option>
              ))}
            </select>
            <input
              className="input w-24"
              type="number"
              min={2000}
              max={2100}
              required
              value={form.ano}
              onChange={(e) => setForm({ ...form, ano: Number(e.target.value) })}
            />
          </div>
        </label>
        <button type="submit" className="btn-primary flex items-center gap-2">
          {editandoId === null ? <Plus className="h-4 w-4" /> : <Check className="h-4 w-4" />}
          {editandoId === null ? "Adicionar" : "Salvar"}
        </button>
        {editandoId !== null && (
          <button type="button" className="btn-ghost flex items-center gap-2" onClick={cancelar}>
            <X className="h-4 w-4" /> Cancelar
          </button>
        )}
      </form>
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
