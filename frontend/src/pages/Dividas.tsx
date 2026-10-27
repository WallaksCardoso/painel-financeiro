import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { dividasApi } from "../api";
import ModalTransacao from "../components/formularios/ModalTransacao";
import { novaTransacao } from "../components/formularios/transacao";
import ModalFormulario from "../components/Modal";
import { useCarregar } from "../hooks/useCarregar";
import ProgressBar from "../components/ProgressBar";
import { LABEL_PRIORIDADE, LABEL_SITUACAO } from "../lib/constantes";
import { formatarData, formatarPercentual, formatarReal } from "../lib/formatar";
import { type Divida, type DividaInput } from "../types";

const VAZIO: DividaInput = {
  nome: "",
  valor_inicial: 0,
  total_pago: 0,
  prazo: null,
  status: "em_andamento",
  prioridade: "alta",
  observacao: null,
};

export default function Dividas() {
  const { dados, recarregar } = useCarregar(dividasApi.listar, []);
  const [pagando, setPagando] = useState<Divida | null>(null);
  const dividas = dados ?? [];
  const [criando, setCriando] = useState(false);
  const [editando, setEditando] = useState<Divida | null>(null);

  const totalRestante = dividas
    .filter((d) => d.status !== "concluido")
    .reduce((acc, d) => acc + d.restante, 0);
  const totalPago = dividas.reduce((acc, d) => acc + d.pago_efetivo, 0);
  const totalInicial = dividas.reduce((acc, d) => acc + d.valor_inicial, 0);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dívidas</h1>
          <p className="text-sm text-muted mt-1">Acompanhamento das quitações em andamento</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setCriando(true)}>
          <Plus className="h-4 w-4" /> Nova dívida
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs text-muted">Total inicial</p>
          <p className="text-2xl font-semibold mt-2">{formatarReal(totalInicial)}</p>
        </div>
        <div className="card">
          <p className="text-xs text-muted">Já pago</p>
          <p className="text-2xl font-semibold mt-2 text-success">{formatarReal(totalPago)}</p>
        </div>
        <div className="card">
          <p className="text-xs text-muted">Falta quitar</p>
          <p className="text-2xl font-semibold mt-2 text-danger">{formatarReal(totalRestante)}</p>
        </div>
      </div>

      <div className="space-y-4">
        {dividas.length === 0 && (
          <div className="card text-center text-muted py-12">Sem dívidas cadastradas.</div>
        )}
        {dividas.map((d) => {
          const cor = d.progresso >= 100 ? "success" : "accent";
          return (
            <div key={d.id} className="card">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-lg font-semibold">{d.nome}</h3>
                    <span
                      className={[
                        "badge",
                        d.prioridade === "alta"
                          ? "bg-danger/15 text-danger"
                          : d.prioridade === "media"
                            ? "bg-warning/15 text-warning"
                            : "bg-white/5 text-muted",
                      ].join(" ")}
                    >
                      {LABEL_PRIORIDADE[d.prioridade]}
                    </span>
                    {d.status === "concluido" && (
                      <span className="badge bg-success/15 text-success">Quitada</span>
                    )}
                  </div>
                  {d.observacao && <p className="text-sm text-muted mt-1">{d.observacao}</p>}
                  {d.prazo && <p className="text-xs text-muted mt-1">Prazo: {formatarData(d.prazo)}</p>}
                </div>
                <div className="flex gap-1 shrink-0">
                  {d.status !== "concluido" && (
                    <button
                      className="btn-primary text-sm py-1.5!"
                      onClick={() => setPagando(d)}
                      title="Cria uma quitação vinculada que abate o saldo desta dívida"
                    >
                      Registrar pagamento
                    </button>
                  )}
                  <button className="btn-ghost text-sm py-1.5!" onClick={() => setEditando(d)}>
                    Editar
                  </button>
                  <button
                    className="p-1.5 rounded-sm hover:bg-danger/20 text-danger"
                    onClick={async () => {
                      const aviso =
                        d.pago_vinculado > 0
                          ? `Apagar "${d.nome}"? As quitações já lançadas continuam em Transações, mas deixam de abater esta dívida.`
                          : `Apagar "${d.nome}"?`;
                      if (confirm(aviso)) {
                        await dividasApi.remover(d.id).catch(() => undefined);
                        recarregar();
                      }
                    }}
                    title="Apagar"
                    aria-label="Apagar"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted">
                    {formatarReal(d.pago_efetivo)} / {formatarReal(d.valor_inicial)}
                  </span>
                  <span className="font-medium text-gray-200">{formatarPercentual(d.progresso)}</span>
                </div>
                <ProgressBar valor={d.progresso} cor={cor} altura="lg" />
                <div className="flex justify-between text-xs text-muted">
                  <span>
                    Faltam <span className="text-danger font-semibold">{formatarReal(d.restante)}</span>
                  </span>
                  {d.pago_vinculado > 0 && (
                    <span title="Soma das quitações lançadas em Transações e vinculadas a esta dívida">
                      {formatarReal(d.pago_vinculado)} via quitações
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {pagando && (
        <ModalTransacao
          inicial={novaTransacao({
            lancamento: pagando.nome,
            tipo: "quitacao",
            categoria: "quitacao",
            valor: pagando.restante,
            divida_id: pagando.id,
          })}
          editando={null}
          aoFechar={() => setPagando(null)}
          aoSalvar={() => {
            setPagando(null);
            recarregar();
          }}
        />
      )}

      {(criando || editando) && (
        <ModalDivida
          inicial={editando ? toInput(editando) : VAZIO}
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

function toInput(d: Divida): DividaInput {
  return {
    nome: d.nome,
    valor_inicial: d.valor_inicial,
    total_pago: d.total_pago,
    prazo: d.prazo,
    status: d.status,
    prioridade: d.prioridade,
    observacao: d.observacao,
  };
}

interface ModalProps {
  inicial: DividaInput;
  editando: Divida | null;
  aoFechar: () => void;
  aoSalvar: () => void;
}

function ModalDivida({ inicial, editando, aoFechar, aoSalvar }: ModalProps) {
  const [form, setForm] = useState<DividaInput>(inicial);

  function update<K extends keyof DividaInput>(campo: K, valor: DividaInput[K]) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  async function salvar() {
    if (editando) {
      const { status, ...resto } = form;
      await dividasApi.atualizar(editando.id, status === editando.status ? resto : form);
    } else {
      await dividasApi.criar(form);
    }
    aoSalvar();
  }

  return (
    <ModalFormulario
      titulo={editando ? "Editar dívida" : "Nova dívida"}
      aoFechar={aoFechar}
      aoEnviar={salvar}
      textoSalvar={editando ? "Salvar" : "Criar"}
    >
      <label className="block">
        <span className="text-xs text-muted">Nome</span>
        <input
          className="input w-full mt-1"
          required
          value={form.nome}
          onChange={(e) => update("nome", e.target.value)}
        />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label>
          <span className="text-xs text-muted">Valor inicial (R$)</span>
          <input
            className="input w-full mt-1"
            type="number"
            step="0.01"
            min={0.01}
            required
            value={form.valor_inicial}
            onChange={(e) => update("valor_inicial", Number(e.target.value))}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Já pago à parte (R$)</span>
          <input
            className="input w-full mt-1"
            type="number"
            step="0.01"
            min={0}
            max={form.valor_inicial || undefined}
            value={form.total_pago}
            onChange={(e) => update("total_pago", Number(e.target.value))}
            title="Valor já quitado sem registrar em Transações. Quitações vinculadas somam automaticamente."
          />
        </label>
        <label>
          <span className="text-xs text-muted">Prazo</span>
          <input
            className="input w-full mt-1"
            type="date"
            value={form.prazo ?? ""}
            onChange={(e) => update("prazo", e.target.value || null)}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Prioridade</span>
          <select
            className="input w-full mt-1"
            value={form.prioridade}
            onChange={(e) => update("prioridade", e.target.value as DividaInput["prioridade"])}
          >
            <option value="alta">Alta</option>
            <option value="media">Média</option>
            <option value="baixa">Baixa</option>
          </select>
        </label>
        {editando && (
          <label className="col-span-2">
            <span className="text-xs text-muted">Situação</span>
            <select
              className="input w-full mt-1"
              value={form.status}
              onChange={(e) => update("status", e.target.value as DividaInput["status"])}
            >
              {(Object.keys(LABEL_SITUACAO) as DividaInput["status"][]).map((s) => (
                <option key={s} value={s}>
                  {s === "concluido" ? "Quitada" : LABEL_SITUACAO[s]}
                </option>
              ))}
            </select>
            <span className="text-[11px] text-muted mt-1 block">
              Marque "Quitada" para encerrar à mão (ex.: dívida perdoada).
            </span>
          </label>
        )}
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
