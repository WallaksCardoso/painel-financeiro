import { AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";
import { Fragment, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { projecaoApi } from "../api";
import Card from "../components/Card";
import { useCarregar } from "../hooks/useCarregar";
import { CORES, estiloTooltip } from "../lib/tema";
import { MES_CURTO, NOMES_MESES } from "../lib/constantes";
import { formatarReal } from "../lib/formatar";
import { type GrupoProjecao, type ProjecaoMes } from "../types";

const OPCOES_MESES = [6, 12, 24];

const LABEL_GRUPO: Record<GrupoProjecao, string> = {
  entrada: "Entrada",
  conta: "Conta",
  quitacao: "Quitação",
  investimento: "Investimento",
  cartao: "Cartão",
  beneficio: "Benefício",
};

const COR_GRUPO: Record<GrupoProjecao, string> = {
  entrada: "bg-success/15 text-success",
  conta: "bg-danger/15 text-danger",
  quitacao: "bg-white/[0.08] text-gray-100",
  investimento: "bg-warning/15 text-warning",
  cartao: "bg-white/10 text-gray-200",
  beneficio: "bg-white/5 text-muted",
};

function rotuloMes(m: { mes: number; ano: number }) {
  return `${MES_CURTO[m.mes - 1]}/${String(m.ano).slice(2)}`;
}

export default function Fluxo() {
  const [meses, setMeses] = useState(12);
  const [aberto, setAberto] = useState<string | null>(null);
  const { dados: projecao, erro } = useCarregar(() => projecaoApi.obter(meses), [meses]);

  if (erro && !projecao) {
    return <p className="text-danger">Não foi possível carregar a projeção.</p>;
  }
  if (!projecao) {
    return <p className="text-muted">Carregando projeção…</p>;
  }

  const atual = projecao.meses[0];
  const ultimo = projecao.meses[projecao.meses.length - 1];
  const proximaLiberacao = projecao.meses.find((m) => m.terminando.length > 0);
  const mesesNegativos = projecao.meses.filter((m) => m.sobra < 0).length;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Fluxo de caixa</h1>
          <p className="text-sm text-muted mt-1">
            Quanto sobra em cada mês com o que já está cadastrado hoje
          </p>
        </div>
        <div className="flex gap-1 rounded-lg bg-white/5 p-1">
          {OPCOES_MESES.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setMeses(n)}
              className={[
                "px-3 py-1.5 rounded-md text-sm transition",
                meses === n ? "bg-white/[0.08] text-gray-100" : "text-gray-300 hover:bg-white/10",
              ].join(" ")}
            >
              {n} meses
            </button>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card
          titulo={`Sobra em ${NOMES_MESES[atual.mes - 1]}`}
          valor={formatarReal(atual.sobra)}
          cor={atual.sobra < 0 ? "danger" : "success"}
          legenda={`${formatarReal(atual.entradas)} entram · ${formatarReal(atual.saidas)} saem`}
        />
        <Card
          titulo={`Acumulado até ${rotuloMes(ultimo)}`}
          valor={formatarReal(ultimo.acumulado)}
          cor={ultimo.acumulado < 0 ? "danger" : "accent"}
          legenda="Soma das sobras do período"
        />
        <Card
          titulo="Próxima parcela a acabar"
          valor={proximaLiberacao ? rotuloMes(proximaLiberacao) : "—"}
          cor="warning"
          legenda={
            proximaLiberacao
              ? `${proximaLiberacao.terminando.map((t) => t.descricao).join(", ")} · libera ${formatarReal(
                  proximaLiberacao.terminando.reduce((s, t) => s + t.valor_parcela, 0),
                )}/mês`
              : "Nenhuma parcela termina no período"
          }
        />
        <Card
          titulo="Meses no vermelho"
          valor={String(mesesNegativos)}
          cor={mesesNegativos > 0 ? "danger" : "muted"}
          legenda={mesesNegativos > 0 ? "Saídas maiores que entradas" : "Nenhum no período"}
        />
      </div>

      {projecao.sem_valor.length > 0 && (
        <div className="card py-3! flex items-start gap-3 border-warning/30">
          <AlertTriangle className="h-4 w-4 text-warning mt-0.5 shrink-0" />
          <p className="text-sm text-gray-300">
            <span className="font-medium text-warning">Sem valor definido</span> (não entram na conta):{" "}
            {projecao.sem_valor.join(", ")}
          </p>
        </div>
      )}

      <GraficoSobra meses={projecao.meses} />

      <div className="card p-0! overflow-x-auto">
        <div className="p-4 border-b border-white/5">
          <h3 className="font-semibold">Mês a mês</h3>
          <p className="text-xs text-muted mt-0.5">
            Clique num mês para ver os lançamentos. "Previsto" = mensal ainda não lançado, repetido do último
            mês.
          </p>
        </div>
        <table className="w-full text-sm min-w-[860px]">
          <thead className="bg-white/5 text-xs text-muted">
            <tr>
              <th className="text-left px-4 py-3">Mês</th>
              <th className="text-right px-4 py-3">Entradas</th>
              <th className="text-right px-4 py-3">Contas</th>
              <th className="text-right px-4 py-3">Quitações</th>
              <th className="text-right px-4 py-3">Cartão</th>
              <th className="text-right px-4 py-3">Investim.</th>
              <th className="text-right px-4 py-3">Sobra</th>
              <th className="text-right px-4 py-3">Acumulado</th>
            </tr>
          </thead>
          <tbody>
            {projecao.meses.map((m) => {
              const chave = `${m.ano}-${m.mes}`;
              const expandido = aberto === chave;
              return (
                <Fragment key={chave}>
                  <tr
                    className="border-t border-white/5 hover:bg-white/5 cursor-pointer"
                    onClick={() => setAberto(expandido ? null : chave)}
                  >
                    <td className="px-4 py-3 font-medium">
                      <div className="flex items-center gap-2">
                        {expandido ? (
                          <ChevronDown className="h-4 w-4 text-muted" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-muted" />
                        )}
                        {NOMES_MESES[m.mes - 1]} {m.ano}
                        {m.terminando.length > 0 && (
                          <span className="badge bg-warning/15 text-warning">
                            {m.terminando.length === 1
                              ? "parcela acaba"
                              : `${m.terminando.length} parcelas acabam`}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-success">
                      {formatarReal(m.entradas)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-300">
                      {formatarReal(m.contas)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-300">
                      {formatarReal(m.quitacoes)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-300">
                      {formatarReal(m.cartao)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-300">
                      {formatarReal(m.investimentos)}
                    </td>
                    <td
                      className={[
                        "px-4 py-3 text-right tabular-nums font-semibold",
                        m.sobra < 0 ? "text-danger" : "text-gray-100",
                      ].join(" ")}
                    >
                      {formatarReal(m.sobra)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-muted">
                      {formatarReal(m.acumulado)}
                    </td>
                  </tr>
                  {expandido && <DetalheMes mes={m} />}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3 className="font-semibold">Parcelas em andamento</h3>
        <p className="text-xs text-muted mt-0.5 mb-4">Ordenadas pelo mês em que acabam</p>
        {projecao.parcelas_ativas.length === 0 ? (
          <p className="text-sm text-muted py-4 text-center">Nenhuma compra parcelada em andamento.</p>
        ) : (
          <ul className="space-y-3">
            {projecao.parcelas_ativas.map((p) => (
              <li key={p.compra_id} className="flex flex-wrap items-center gap-x-4 gap-y-1">
                <div className="min-w-[200px] flex-1">
                  <p className="font-medium">{p.descricao}</p>
                  <p className="text-xs text-muted">
                    {p.cartao_nome} ·{" "}
                    {p.parcela_atual === 0
                      ? `começa em ${MES_CURTO[p.comeca_mes - 1]}/${String(p.comeca_ano).slice(2)} (${p.parcelas_total}×)`
                      : `parcela ${p.parcela_atual} de ${p.parcelas_total}`}
                  </p>
                </div>
                <div className="w-40 h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-accent"
                    style={{ width: `${(p.parcela_atual / p.parcelas_total) * 100}%` }}
                  />
                </div>
                <p className="w-28 text-right tabular-nums">{formatarReal(p.valor_parcela)}/mês</p>
                <p className="w-28 text-right text-sm text-muted">
                  acaba {MES_CURTO[p.termina_mes - 1]}/{String(p.termina_ano).slice(2)}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function DetalheMes({ mes }: { mes: ProjecaoMes }) {
  return (
    <tr className="bg-black/20">
      <td colSpan={8} className="px-4 py-4">
        {mes.terminando.length > 0 && (
          <p className="text-sm text-warning mb-3">
            Última parcela:{" "}
            {mes.terminando.map((t) => `${t.descricao} (${formatarReal(t.valor_parcela)})`).join(", ")} — a
            partir do mês seguinte esse valor fica livre.
          </p>
        )}
        {mes.linhas.length === 0 ? (
          <p className="text-sm text-muted">Nada lançado nem previsto neste mês.</p>
        ) : (
          <table className="w-full text-sm">
            <tbody>
              {mes.linhas.map((l, i) => (
                <tr key={i} className="border-t border-white/5 first:border-t-0">
                  <td className="py-1.5 w-14 text-muted tabular-nums">{l.dia ? `dia ${l.dia}` : ""}</td>
                  <td className="py-1.5">
                    {l.descricao}
                    {l.previsto && <span className="badge bg-white/5 text-muted ml-2">previsto</span>}
                  </td>
                  <td className="py-1.5 w-32">
                    <span className={["badge", COR_GRUPO[l.grupo]].join(" ")}>{LABEL_GRUPO[l.grupo]}</span>
                  </td>
                  <td
                    className={[
                      "py-1.5 w-32 text-right tabular-nums",
                      l.grupo === "entrada"
                        ? "text-success"
                        : l.grupo === "beneficio"
                          ? "text-muted"
                          : "text-gray-200",
                    ].join(" ")}
                    title={l.grupo === "beneficio" ? "Benefício: não entra no saldo" : undefined}
                  >
                    {l.grupo === "entrada" || l.grupo === "beneficio" ? "+" : "−"} {formatarReal(l.valor)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </td>
    </tr>
  );
}

function GraficoSobra({ meses }: { meses: ProjecaoMes[] }) {
  const dados = meses.map((m) => ({ ...m, rotulo: rotuloMes(m) }));
  return (
    <div className="card">
      <h3 className="font-semibold">Sobra por mês</h3>
      <p className="text-xs text-muted mt-0.5 mb-4">
        Entradas menos tudo que sai (contas, quitações, investimentos e fatura)
      </p>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={dados} margin={{ left: 8, right: 8 }} barCategoryGap="25%">
            <CartesianGrid vertical={false} stroke={CORES.grade} />
            <XAxis dataKey="rotulo" stroke={CORES.eixo} fontSize={11} tickLine={false} axisLine={false} />
            <YAxis
              stroke={CORES.eixo}
              fontSize={11}
              tickLine={false}
              axisLine={false}
              width={70}
              tickFormatter={(v: number) => formatarReal(v).replace(",00", "")}
            />
            <ReferenceLine y={0} stroke={CORES.eixo} />
            <Tooltip
              cursor={{ fill: CORES.grade }}
              contentStyle={estiloTooltip}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const m = payload[0].payload as ProjecaoMes & { rotulo: string };
                return (
                  <div style={estiloTooltip} className="px-3 py-2 space-y-0.5">
                    <p className="font-semibold text-gray-100">
                      {NOMES_MESES[m.mes - 1]} {m.ano}
                    </p>
                    <p className="text-gray-300">Entradas: {formatarReal(m.entradas)}</p>
                    <p className="text-gray-300">Saídas: {formatarReal(m.saidas)}</p>
                    <p className="text-gray-100 font-medium">Sobra: {formatarReal(m.sobra)}</p>
                  </div>
                );
              }}
            />
            <Bar dataKey="sobra" radius={[3, 3, 0, 0]} maxBarSize={28}>
              {dados.map((m) => (
                <Cell key={`${m.ano}-${m.mes}`} fill={m.sobra < 0 ? CORES.negativo : CORES.acento} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
