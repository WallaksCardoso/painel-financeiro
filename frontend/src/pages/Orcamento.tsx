import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { orcamentoApi } from "../api";
import { usePeriodo } from "../contexts/Periodo";
import ModalFormulario from "../components/Modal";
import SeletorMes from "../components/SeletorMes";
import { useOpcoes } from "../contexts/Opcoes";
import { useCarregar } from "../hooks/useCarregar";
import ProgressBar from "../components/ProgressBar";
import { NOMES_MESES } from "../lib/constantes";
import { formatarPercentual, formatarReal } from "../lib/formatar";
import { type OrcamentoInput } from "../types";

const STATUS_LABEL = {
  ok: { texto: "Ok", classe: "bg-success/15 text-success" },
  atencao: { texto: "Atenção", classe: "bg-warning/15 text-warning" },
  estourou: { texto: "Estourou", classe: "bg-danger/15 text-danger" },
};

export default function Orcamento() {
  const { rotulo } = useOpcoes();
  const { mes, ano, setPeriodo } = usePeriodo();
  const { dados, recarregar } = useCarregar(() => orcamentoApi.listar(mes, ano), [mes, ano]);
  const itens = dados ?? [];
  const [criando, setCriando] = useState(false);

  const totalTeto = itens.reduce((s, i) => s + i.teto, 0);
  const totalGasto = itens.reduce((s, i) => s + i.gasto, 0);

  async function atualizarTeto(campo: HTMLInputElement, id: number, tetoAtual: number) {
    const novo = Number(campo.value);
    if (novo === tetoAtual) return;
    try {
      await orcamentoApi.atualizar(id, { teto: novo });
      recarregar();
    } catch {
      campo.value = String(tetoAtual);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Orçamento</h1>
          <p className="text-sm text-muted mt-1">
            Tetos por categoria — {NOMES_MESES[mes - 1]} de {ano} · inclui compras no cartão
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SeletorMes mes={mes} ano={ano} aoMudar={setPeriodo} />
          <button className="btn-primary flex items-center gap-2" onClick={() => setCriando(true)}>
            <Plus className="h-4 w-4" /> Categoria
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs text-muted">Total orçado</p>
          <p className="text-2xl font-semibold mt-2">{formatarReal(totalTeto)}</p>
        </div>
        <div className="card">
          <p className="text-xs text-muted">Total gasto</p>
          <p
            className={["text-2xl font-semibold mt-2", totalGasto > totalTeto ? "text-danger" : ""].join(" ")}
          >
            {formatarReal(totalGasto)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-muted">Disponível</p>
          <p
            className={[
              "text-2xl font-semibold mt-2",
              totalTeto - totalGasto >= 0 ? "text-success" : "text-danger",
            ].join(" ")}
          >
            {formatarReal(totalTeto - totalGasto)}
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {itens.length === 0 && (
          <div className="card text-center text-muted py-12">
            Nenhuma categoria orçada para este mês. Crie uma pra começar.
          </div>
        )}
        {itens.map((i) => {
          const status = STATUS_LABEL[i.status];
          return (
            <div key={i.id} className="card">
              <div className="flex items-center justify-between gap-4 mb-3">
                <div>
                  <h3 className="font-semibold">{rotulo("categoria", i.categoria)}</h3>
                  <p className="text-xs text-muted mt-0.5">
                    {formatarReal(i.gasto)} de {formatarReal(i.teto)} — {formatarPercentual(i.uso_percentual)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={["badge", status.classe].join(" ")}>{status.texto}</span>
                  <input
                    className="input w-32 text-right"
                    type="number"
                    step="0.01"
                    min={0}
                    defaultValue={i.teto}
                    aria-label={`Teto de ${rotulo("categoria", i.categoria)}`}
                    onBlur={(e) => atualizarTeto(e.currentTarget, i.id, i.teto)}
                    title="Edite o teto e clique fora pra salvar"
                  />
                  <button
                    className="p-1.5 rounded-sm hover:bg-danger/20 text-danger"
                    onClick={async () => {
                      if (confirm(`Apagar orçamento de ${i.categoria}?`)) {
                        await orcamentoApi.remover(i.id).catch(() => undefined);
                        recarregar();
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <ProgressBar
                valor={i.uso_percentual}
                cor={i.status === "estourou" ? "danger" : i.status === "atencao" ? "warning" : "success"}
                altura="md"
              />
            </div>
          );
        })}
      </div>

      {criando && (
        <ModalOrcamento
          mes={mes}
          ano={ano}
          aoFechar={() => setCriando(false)}
          aoSalvar={() => {
            setCriando(false);
            recarregar();
          }}
        />
      )}
    </div>
  );
}

function ModalOrcamento({
  mes,
  ano,
  aoFechar,
  aoSalvar,
}: {
  mes: number;
  ano: number;
  aoFechar: () => void;
  aoSalvar: () => void;
}) {
  const { lista } = useOpcoes();
  const [form, setForm] = useState<OrcamentoInput>({
    mes,
    ano,
    categoria: "comida",
    teto: 0,
  });

  async function salvar() {
    await orcamentoApi.criar(form);
    aoSalvar();
  }

  return (
    <ModalFormulario
      titulo={"Nova categoria orçada"}
      aoFechar={aoFechar}
      aoEnviar={salvar}
      textoSalvar={"Criar"}
    >
      <div className="grid grid-cols-2 gap-3">
        <label>
          <span className="text-xs text-muted">Mês</span>
          <select
            className="input w-full mt-1"
            value={form.mes}
            onChange={(e) => setForm({ ...form, mes: Number(e.target.value) })}
          >
            {NOMES_MESES.map((nome, i) => (
              <option key={nome} value={i + 1}>
                {nome}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="text-xs text-muted">Ano</span>
          <input
            className="input w-full mt-1"
            type="number"
            value={form.ano}
            onChange={(e) => setForm({ ...form, ano: Number(e.target.value) })}
          />
        </label>
        <label className="col-span-2">
          <span className="text-xs text-muted">Categoria</span>
          <select
            className="input w-full mt-1"
            value={form.categoria}
            onChange={(e) => setForm({ ...form, categoria: e.target.value })}
          >
            {lista("categoria").map((c) => (
              <option key={c.chave} value={c.chave}>
                {c.nome}
              </option>
            ))}
          </select>
        </label>
        <label className="col-span-2">
          <span className="text-xs text-muted">Teto (R$)</span>
          <input
            className="input w-full mt-1"
            type="number"
            step="0.01"
            required
            value={form.teto}
            onChange={(e) => setForm({ ...form, teto: Number(e.target.value) })}
          />
        </label>
      </div>
    </ModalFormulario>
  );
}
