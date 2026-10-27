import { Pencil, Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { configApi, reservaApi } from "../api";
import ModalFormulario from "../components/Modal";
import { useOpcoes } from "../contexts/Opcoes";
import { useCarregar } from "../hooks/useCarregar";
import { CORES, estiloTooltip } from "../lib/tema";
import { hojeISO } from "../lib/datas";
import Card from "../components/Card";
import ProgressBar from "../components/ProgressBar";
import { formatarData, formatarPercentual, formatarReal, formatarRealCurto } from "../lib/formatar";
import type { MovimentoReserva, MovimentoReservaInput } from "../types";

const novoMovimento = (): MovimentoReservaInput => ({
  descricao: "",
  tipo: "aporte",
  valor: 0,
  data: hojeISO(),
  origem: "salario",
  observacao: null,
});

export default function Reserva() {
  const { rotulo } = useOpcoes();
  const metaCarga = useCarregar(() => configApi.ler("meta_reserva"), []);
  const metaNumero = Number(metaCarga.dados);
  const meta = metaCarga.dados && Number.isFinite(metaNumero) && metaNumero > 0 ? metaNumero : null;
  const [editandoMeta, setEditandoMeta] = useState(false);
  const { dados, recarregar } = useCarregar(() => Promise.all([reservaApi.listar(), reservaApi.saldo()]), []);
  const [movimentos, saldo] = dados ?? [[], null];
  const [criando, setCriando] = useState(false);
  const [editando, setEditando] = useState<MovimentoReserva | null>(null);

  const evolucao = useMemo(() => {
    const ordenados = [...movimentos].sort((a, b) => a.data.localeCompare(b.data));
    const centavos = ordenados.map((m) => Math.round(m.valor * 100) * (m.tipo === "aporte" ? 1 : -1));
    return ordenados.map((m, i) => ({
      data: formatarData(m.data),
      saldo: centavos.slice(0, i + 1).reduce((soma, c) => soma + c, 0) / 100,
    }));
  }, [movimentos]);

  const progressoMeta = saldo && meta ? Math.min((saldo.saldo / meta) * 100, 100) : 0;

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Reserva de Emergência</h1>
          <p className="text-sm text-muted mt-1">Colchão para imprevistos</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => setEditandoMeta(true)}>
            {meta ? "Editar meta" : "Definir meta"}
          </button>
          <button className="btn-primary flex items-center gap-2" onClick={() => setCriando(true)}>
            <Plus className="h-4 w-4" /> Novo movimento
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card
          titulo="Saldo atual"
          valor={formatarReal(saldo?.saldo ?? 0)}
          cor="muted"
          legenda={meta ? `Meta: ${formatarReal(meta)}` : "Sem meta definida"}
        />
        <Card titulo="Total aportado" valor={formatarReal(saldo?.total_aportes ?? 0)} cor="success" />
        <Card titulo="Total sacado" valor={formatarReal(saldo?.total_saques ?? 0)} cor="danger" />
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Progresso até a meta</h3>
          <span className="text-sm text-accent-glow">{formatarPercentual(progressoMeta)}</span>
        </div>
        <ProgressBar valor={progressoMeta} altura="lg" />
      </div>

      <div className="card">
        <h3 className="font-semibold mb-4">Evolução do saldo</h3>
        {evolucao.length === 0 ? (
          <p className="text-muted text-sm">Sem movimentos registrados ainda.</p>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={evolucao}>
              <CartesianGrid stroke={CORES.grade} />
              <XAxis dataKey="data" stroke={CORES.eixo} fontSize={11} padding={{ left: 24, right: 24 }} />
              <YAxis stroke={CORES.eixo} fontSize={11} width={70} tickFormatter={formatarRealCurto} />
              <Tooltip formatter={(v) => formatarReal(Number(v))} contentStyle={estiloTooltip} />
              <Line
                type="monotone"
                dataKey="saldo"
                name="Saldo"
                stroke={CORES.acento}
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="card p-0! overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-white/5 text-xs text-muted">
            <tr>
              <th className="text-left px-4 py-3">Descrição</th>
              <th className="text-left px-4 py-3">Tipo</th>
              <th className="text-right px-4 py-3">Valor</th>
              <th className="text-left px-4 py-3">Data</th>
              <th className="text-left px-4 py-3">Origem</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {movimentos.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center text-muted py-8">
                  Nenhum movimento.
                </td>
              </tr>
            )}
            {movimentos.map((m) => (
              <tr key={m.id} className="border-t border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 font-medium">{m.descricao}</td>
                <td className="px-4 py-3">
                  <span
                    className={[
                      "badge",
                      m.tipo === "aporte" ? "bg-success/15 text-success" : "bg-danger/15 text-danger",
                    ].join(" ")}
                  >
                    {m.tipo === "aporte" ? "Aporte" : "Saque"}
                  </span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">{formatarReal(m.valor)}</td>
                <td className="px-4 py-3 text-muted">{formatarData(m.data)}</td>
                <td className="px-4 py-3 text-muted">{rotulo("origem_reserva", m.origem)}</td>
                <td className="px-4 py-3 text-right whitespace-nowrap">
                  <button
                    className="p-1.5 rounded-sm hover:bg-white/10"
                    onClick={() => setEditando(m)}
                    title="Editar"
                    aria-label="Editar movimento"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    className="p-1.5 rounded-sm hover:bg-danger/20 text-danger"
                    title="Apagar"
                    aria-label="Apagar movimento"
                    onClick={async () => {
                      if (confirm("Apagar este movimento?")) {
                        await reservaApi.remover(m.id).catch(() => undefined);
                        recarregar();
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editandoMeta && (
        <ModalMeta
          atual={meta}
          aoFechar={() => setEditandoMeta(false)}
          aoSalvar={() => {
            setEditandoMeta(false);
            metaCarga.recarregar();
          }}
        />
      )}

      {(criando || editando) && (
        <ModalReserva
          editando={editando}
          aoFechar={() => {
            setCriando(false);
            setEditando(null);
          }}
          aoSalvar={() => {
            setCriando(false);
            setEditando(null);
            recarregar();
          }}
        />
      )}
    </div>
  );
}

function ModalReserva({
  editando,
  aoFechar,
  aoSalvar,
}: {
  editando: MovimentoReserva | null;
  aoFechar: () => void;
  aoSalvar: () => void;
}) {
  const { lista } = useOpcoes();
  const [form, setForm] = useState<MovimentoReservaInput>(() =>
    editando
      ? {
          descricao: editando.descricao,
          tipo: editando.tipo,
          valor: editando.valor,
          data: editando.data,
          origem: editando.origem,
          observacao: editando.observacao,
        }
      : novoMovimento(),
  );

  function update<K extends keyof MovimentoReservaInput>(campo: K, valor: MovimentoReservaInput[K]) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  async function salvar() {
    if (editando) await reservaApi.atualizar(editando.id, form);
    else await reservaApi.criar(form);
    aoSalvar();
  }

  return (
    <ModalFormulario
      titulo={editando ? "Editar movimento" : "Novo movimento"}
      aoFechar={aoFechar}
      aoEnviar={salvar}
      textoSalvar={editando ? "Salvar" : "Criar"}
    >
      <label className="block">
        <span className="text-xs text-muted">Descrição</span>
        <input
          className="input w-full mt-1"
          required
          value={form.descricao}
          onChange={(e) => update("descricao", e.target.value)}
        />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label>
          <span className="text-xs text-muted">Tipo</span>
          <select
            className="input w-full mt-1"
            value={form.tipo}
            onChange={(e) => update("tipo", e.target.value as "aporte" | "saque")}
          >
            <option value="aporte">Aporte</option>
            <option value="saque">Saque</option>
          </select>
        </label>
        <label>
          <span className="text-xs text-muted">Valor (R$)</span>
          <input
            className="input w-full mt-1"
            type="number"
            step="0.01"
            min={0.01}
            required
            value={form.valor || ""}
            onChange={(e) => update("valor", Number(e.target.value))}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Data</span>
          <input
            className="input w-full mt-1"
            type="date"
            required
            value={form.data}
            onChange={(e) => update("data", e.target.value)}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Origem</span>
          <select
            className="input w-full mt-1"
            value={form.origem ?? ""}
            onChange={(e) => update("origem", e.target.value || null)}
          >
            <option value="">—</option>
            {lista("origem_reserva").map((o) => (
              <option key={o.chave} value={o.chave}>
                {o.nome}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="block">
        <span className="text-xs text-muted">Observação</span>
        <textarea
          className="input w-full mt-1"
          rows={2}
          value={form.observacao ?? ""}
          onChange={(e) => update("observacao", e.target.value || null)}
        />
      </label>
    </ModalFormulario>
  );
}

function ModalMeta({
  atual,
  aoFechar,
  aoSalvar,
}: {
  atual: number | null;
  aoFechar: () => void;
  aoSalvar: () => void;
}) {
  const [valor, setValor] = useState(atual ?? 0);
  return (
    <ModalFormulario
      titulo="Meta da reserva"
      aoFechar={aoFechar}
      aoEnviar={async () => {
        await configApi.salvar("meta_reserva", String(valor));
        aoSalvar();
      }}
    >
      <label className="block">
        <span className="text-xs text-muted">Quanto você quer ter guardado (R$)</span>
        <input
          className="input w-full mt-1"
          type="number"
          step="0.01"
          min={0}
          required
          value={valor}
          onChange={(e) => setValor(Number(e.target.value))}
        />
      </label>
    </ModalFormulario>
  );
}
