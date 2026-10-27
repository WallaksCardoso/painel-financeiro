import { Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { transacoesApi } from "../api";
import { usePeriodo } from "../contexts/Periodo";
import ModalTransacao from "../components/formularios/ModalTransacao";
import { novaTransacao, transacaoParaInput } from "../components/formularios/transacao";
import SeletorMes from "../components/SeletorMes";
import { useOpcoes } from "../contexts/Opcoes";
import BotaoAcao from "../components/BotaoAcao";
import { useCarregar } from "../hooks/useCarregar";
import { dataPadrao } from "../lib/datas";
import { toast } from "../toast";
import { LABEL_TIPO, NOMES_MESES, rotuloSituacao } from "../lib/constantes";
import { formatarData, formatarReal, plural } from "../lib/formatar";
import type { Transacao } from "../types";

const TIPOS = Object.keys(LABEL_TIPO) as Array<keyof typeof LABEL_TIPO>;

export default function Transacoes() {
  const { lista, rotulo } = useOpcoes();
  const { mes, ano, setPeriodo } = usePeriodo();
  const [tipoFiltro, setTipoFiltro] = useState<string>("");
  const [categoriaFiltro, setCategoriaFiltro] = useState<string>("");
  const [editando, setEditando] = useState<Transacao | null>(null);
  const [criando, setCriando] = useState(false);

  const { dados, recarregar } = useCarregar(
    () =>
      transacoesApi.listar({
        mes,
        ano,
        tipo: tipoFiltro || undefined,
        categoria: categoriaFiltro || undefined,
      }),
    [mes, ano, tipoFiltro, categoriaFiltro],
  );
  const transacoes = useMemo(() => dados ?? [], [dados]);

  const totais = useMemo(() => {
    const r = { receita: 0, despesa: 0, quitacao: 0, investimento: 0, beneficio: 0 };
    transacoes.forEach((t) => {
      r[t.tipo] += t.valor;
    });
    return r;
  }, [transacoes]);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Transações</h1>
          <p className="text-sm text-muted mt-1">
            Lançamentos de {NOMES_MESES[mes - 1]} de {ano}
          </p>
        </div>
        <div className="flex gap-2">
          <BotaoAcao
            className="btn-ghost flex items-center gap-2"
            title="Cria os lançamentos que se repetem (mensais e parcelados) que ainda não existem neste mês"
            acao={async () => {
              const criadas = await transacoesApi.gerarRecorrentes(mes, ano);
              if (criadas.length > 0) {
                toast.sucesso(`${plural(criadas.length, "lançamento gerado", "lançamentos gerados")}.`);
                recarregar();
              } else {
                toast.info("Nenhum recorrente pendente para este mês.");
              }
            }}
          >
            <RefreshCw className="h-4 w-4" /> Gerar recorrentes
          </BotaoAcao>
          <button className="btn-primary flex items-center gap-2" onClick={() => setCriando(true)}>
            <Plus className="h-4 w-4" /> Nova transação
          </button>
        </div>
      </header>

      <div className="card flex flex-wrap gap-3">
        <SeletorMes mes={mes} ano={ano} aoMudar={setPeriodo} />
        <select className="input" value={tipoFiltro} onChange={(e) => setTipoFiltro(e.target.value)}>
          <option value="">Todos os tipos</option>
          {TIPOS.map((t) => (
            <option key={t} value={t}>
              {LABEL_TIPO[t]}
            </option>
          ))}
        </select>
        <select
          className="input"
          value={categoriaFiltro}
          onChange={(e) => setCategoriaFiltro(e.target.value)}
        >
          <option value="">Todas as categorias</option>
          {lista("categoria").map((c) => (
            <option key={c.chave} value={c.chave}>
              {c.nome}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
        <div className="card p-4!">
          <p className="text-muted text-xs">Receitas</p>
          <p className="text-success font-semibold mt-1">{formatarReal(totais.receita)}</p>
        </div>
        <div className="card p-4!">
          <p className="text-muted text-xs">Despesas</p>
          <p className="text-gray-100 font-semibold mt-1">{formatarReal(totais.despesa)}</p>
        </div>
        <div className="card p-4!">
          <p className="text-muted text-xs">Quitações</p>
          <p className="text-gray-100 font-semibold mt-1">{formatarReal(totais.quitacao)}</p>
        </div>
        <div className="card p-4!">
          <p className="text-muted text-xs">Investimentos</p>
          <p className="text-gray-100 font-semibold mt-1">{formatarReal(totais.investimento)}</p>
        </div>
        <div className="card p-4!" title="Vale-alimentação, vale-refeição e similares: não entram no saldo">
          <p className="text-muted text-xs">Benefícios</p>
          <p className="text-gray-100 font-semibold mt-1">{formatarReal(totais.beneficio)}</p>
        </div>
      </div>

      <div className="card p-0! overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-white/5 text-xs text-muted">
            <tr>
              <th className="text-left px-4 py-3">Lançamento</th>
              <th className="text-left px-4 py-3">Categoria</th>
              <th className="text-left px-4 py-3">Tipo</th>
              <th className="text-right px-4 py-3">Valor</th>
              <th className="text-left px-4 py-3">Data</th>
              <th className="text-left px-4 py-3">Situação</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {transacoes.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center text-muted py-8">
                  Nenhum lançamento neste filtro.
                </td>
              </tr>
            )}
            {transacoes.map((t) => (
              <tr key={t.id} className="border-t border-white/5 hover:bg-white/5 transition">
                <td className="px-4 py-3 font-medium">{t.lancamento}</td>
                <td className="px-4 py-3 text-muted">{rotulo("categoria", t.categoria)}</td>
                <td className="px-4 py-3">
                  <span className="text-gray-300">{LABEL_TIPO[t.tipo]}</span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">{formatarReal(t.valor)}</td>
                <td className="px-4 py-3 text-muted">{formatarData(t.data)}</td>
                <td className="px-4 py-3">
                  <span
                    className={[
                      "badge",
                      t.situacao === "concluido"
                        ? "bg-success/15 text-success"
                        : t.situacao === "em_andamento"
                          ? "bg-white/[0.08] text-gray-100"
                          : "bg-white/5 text-muted",
                    ].join(" ")}
                  >
                    {rotuloSituacao(t.situacao, t.tipo)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 justify-end">
                    <button
                      className="p-1.5 rounded-sm hover:bg-white/10"
                      onClick={() => setEditando(t)}
                      title="Editar"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      className="p-1.5 rounded-sm hover:bg-danger/20 text-danger"
                      onClick={async () => {
                        if (confirm(`Apagar "${t.lancamento}"?`)) {
                          await transacoesApi.remover(t.id).catch(() => undefined);
                          recarregar();
                        }
                      }}
                      title="Apagar"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(criando || editando) && (
        <ModalTransacao
          inicial={editando ? transacaoParaInput(editando) : novaTransacao({ data: dataPadrao(mes, ano) })}
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
