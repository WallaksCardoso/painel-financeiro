import { Receipt, TrendingUp } from "lucide-react";

import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { configApi, dashboardApi, dividasApi } from "../api";
import { usePeriodo } from "../contexts/Periodo";
import Card from "../components/Card";
import ProgressBar from "../components/ProgressBar";
import SeletorMes from "../components/SeletorMes";
import { useOpcoes } from "../contexts/Opcoes";
import { useCarregar } from "../hooks/useCarregar";
import { CORES, estiloTooltip } from "../lib/tema";
import { NOMES_MESES } from "../lib/constantes";
import { formatarDataCurta, formatarPercentual, formatarReal, formatarRealCurto } from "../lib/formatar";

export default function Dashboard() {
  const { rotulo } = useOpcoes();
  const { mes, ano, setPeriodo } = usePeriodo();
  const config = useCarregar(() => configApi.ler("dias_proximas_contas"), []);
  const diasProximas = config.dados ?? "15";
  const carga = useCarregar(
    () => Promise.all([dashboardApi.completo(mes, ano), dividasApi.listar()]),
    [mes, ano],
  );

  if (carga.erro && !carga.dados) {
    return (
      <div className="card text-center text-muted py-12">
        Não consegui carregar os dados. Verifique se o backend está rodando e recarregue a página.
      </div>
    );
  }

  if (!carga.dados) {
    return <p className="text-muted">Carregando…</p>;
  }
  const [dados, dividas] = carga.dados;

  const distribuicao = [
    { nome: "Entradas", valor: dados.resumo.entradas },
    { nome: "Investimentos", valor: dados.resumo.investimentos },
    { nome: "Despesas", valor: dados.resumo.saidas },
    { nome: "Cartão", valor: dados.resumo.cartao },
    { nome: "Quitações", valor: dados.resumo.quitacoes },
  ].filter((d) => d.valor > 0);

  const categoriasComLabel = dados.por_categoria.map((c) => ({
    ...c,
    label: rotulo("categoria", c.categoria),
  }));

  const tudoZerado =
    dados.resumo.entradas === 0 &&
    dados.resumo.saidas === 0 &&
    dados.fatura_aberta === 0 &&
    dados.proximas_contas.length === 0 &&
    dividas.length === 0 &&
    dados.saldo_reserva === 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-muted">Dashboard</p>
          <h1 className="text-2xl font-semibold tracking-tight">
            {NOMES_MESES[mes - 1]} de {ano}
          </h1>
        </div>
        <div className="flex gap-2">
          <SeletorMes mes={mes} ano={ano} aoMudar={setPeriodo} />
        </div>
      </header>

      {tudoZerado && <BoasVindas />}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card titulo="Entradas" valor={formatarReal(dados.resumo.entradas)} cor="success" />
        <Card
          titulo="Contas"
          valor={formatarReal(dados.resumo.saidas)}
          cor="muted"
          legenda="Despesas lançadas e previstas, pagas ou não"
        />
        <Card
          titulo="Saldo do mês"
          valor={formatarReal(dados.resumo.saldo)}
          cor={dados.resumo.saldo >= 0 ? "accent" : "danger"}
          legenda="Entradas − contas − quitações − investimentos − fatura (igual ao Fluxo)"
        />
        <Card
          titulo="Reserva"
          valor={formatarReal(dados.saldo_reserva)}
          cor="muted"
          legenda="Saldo total (não muda com o mês)"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/cartoes" className="card hover:bg-bg-hover transition-colors">
          <p className="text-sm text-muted">Fatura a pagar, todos os cartões</p>
          <p className="mt-1.5 text-2xl font-semibold tracking-tight">{formatarReal(dados.fatura_aberta)}</p>
          <p className="mt-1 text-xs text-muted">
            Faturas que vencem em {NOMES_MESES[mes - 1]} e ainda não foram pagas
          </p>
        </Link>
        <Link to="/dividas" className="card hover:bg-bg-hover transition-colors">
          <p className="text-sm text-muted">Dívidas a quitar</p>
          <p className="mt-1.5 text-2xl font-semibold tracking-tight">
            {formatarReal(dados.total_dividas_restante)}
          </p>
          <p className="mt-1 text-xs text-muted">
            {dividas.filter((d) => d.status !== "concluido").length} em andamento
          </p>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <div className="card">
            <h3 className="font-semibold mb-4">Distribuição do mês</h3>
            {distribuicao.length === 0 ? (
              <EmptyChart texto="Sem lançamentos concluídos neste mês" Icon={TrendingUp} />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={distribuicao}
                    dataKey="valor"
                    nameKey="nome"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                  >
                    {distribuicao.map((_, i) => (
                      <Cell key={i} fill={CORES.series[i % CORES.series.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatarReal(Number(v))} contentStyle={estiloTooltip} />
                  <Legend
                    itemSorter={null}
                    formatter={(nome) => <span className="text-gray-300">{nome}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="card">
            <h3 className="font-semibold mb-4">Gasto por categoria</h3>
            {categoriasComLabel.length === 0 ? (
              <EmptyChart texto="Sem despesas neste mês" Icon={Receipt} />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={categoriasComLabel} margin={{ left: -10 }}>
                  <XAxis
                    dataKey="label"
                    stroke={CORES.eixo}
                    fontSize={11}
                    angle={-25}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis stroke={CORES.eixo} fontSize={11} width={70} tickFormatter={formatarRealCurto} />
                  <Tooltip formatter={(v) => formatarReal(Number(v))} contentStyle={estiloTooltip} />
                  <Bar dataKey="total" fill={CORES.acento} radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Próximas contas</h3>
              <span className="text-xs text-muted">{diasProximas} dias</span>
            </div>
            {dados.proximas_contas.length === 0 ? (
              <p className="text-sm text-muted text-center py-6">Nada vencendo nos próximos dias.</p>
            ) : (
              <ul className="space-y-3">
                {dados.proximas_contas.slice(0, 8).map((c) => (
                  <li key={c.id} className="flex items-start gap-3 text-sm">
                    <div
                      className={[
                        "shrink-0 h-9 w-9 rounded-lg flex flex-col items-center justify-center text-[10px] font-semibold leading-tight",
                        c.dias_ate_vencer <= 2
                          ? "bg-danger/20 text-danger"
                          : c.dias_ate_vencer <= 7
                            ? "bg-warning/20 text-warning"
                            : "bg-white/5 text-muted",
                      ].join(" ")}
                    >
                      {formatarDataCurta(c.data)
                        .split("/")
                        .map((p, i) => (
                          <span key={i}>{p}</span>
                        ))}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium truncate">{c.lancamento}</p>
                      <p className="text-xs text-muted">
                        {c.categoria ? rotulo("categoria", c.categoria) : "Cartão"} ·{" "}
                        {c.dias_ate_vencer === 0
                          ? "vence hoje"
                          : c.dias_ate_vencer === 1
                            ? "vence amanhã"
                            : `em ${c.dias_ate_vencer} dias`}
                      </p>
                    </div>
                    <p className="text-sm tabular-nums text-danger">{formatarReal(c.valor)}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Quitações</h3>
              <Link to="/dividas" className="text-xs text-accent-glow hover:underline">
                Ver tudo
              </Link>
            </div>
            {dividas.length === 0 ? (
              <p className="text-sm text-muted text-center py-6">Sem dívidas registradas.</p>
            ) : (
              <ul className="space-y-3">
                {dividas.slice(0, 4).map((d) => (
                  <li key={d.id}>
                    <div className="flex items-center justify-between text-sm mb-1.5">
                      <span className="font-medium truncate">{d.nome}</span>
                      <span className="text-accent-glow text-xs">{formatarPercentual(d.progresso)}</span>
                    </div>
                    <ProgressBar
                      valor={d.progresso}
                      cor={d.progresso >= 100 ? "success" : "accent"}
                      altura="sm"
                    />
                    <p className="text-xs text-muted mt-1">Faltam {formatarReal(d.restante)}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyChart({ texto, Icon }: { texto: string; Icon: React.ElementType }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-muted">
      <Icon className="h-5 w-5 mb-2 opacity-60" />
      <p className="text-sm">{texto}</p>
    </div>
  );
}

function BoasVindas() {
  const atalhos = [
    { to: "/transacoes", titulo: "Lançar receitas e despesas" },
    { to: "/cartoes", titulo: "Cadastrar cartões e compras" },
    { to: "/dividas", titulo: "Acompanhar dívidas" },
    { to: "/orcamento", titulo: "Definir tetos por categoria" },
  ];
  return (
    <div className="card">
      <h2 className="text-base font-semibold">Comece pelo cadastro</h2>
      <p className="text-sm text-muted mt-1">Os números aparecem aqui assim que houver lançamentos.</p>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mt-4">
        {atalhos.map(({ to, titulo }) => (
          <Link
            key={to}
            to={to}
            className="rounded-md border border-white/[0.07] hover:bg-white/[0.04] transition-colors px-3 py-2.5 text-sm"
          >
            {titulo}
          </Link>
        ))}
      </div>
    </div>
  );
}
