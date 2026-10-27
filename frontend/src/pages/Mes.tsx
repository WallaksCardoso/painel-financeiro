import { CalendarX, CreditCard, NotebookPen, Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useState, type ReactNode } from "react";
import { cartoesApi, mesApi, transacoesApi } from "../api";
import BotaoAcao from "../components/BotaoAcao";
import { usePeriodo } from "../contexts/Periodo";
import Card from "../components/Card";
import ModalCompra from "../components/formularios/ModalCompra";
import ModalTransacao from "../components/formularios/ModalTransacao";
import { novaTransacao, transacaoParaInput } from "../components/formularios/transacao";
import ModalFormulario from "../components/Modal";
import SeletorMes from "../components/SeletorMes";
import { useOpcoes } from "../contexts/Opcoes";
import { useCarregar } from "../hooks/useCarregar";
import { NOMES_MESES, rotuloSituacao } from "../lib/constantes";
import { dataPadrao } from "../lib/datas";
import { formatarReal, plural } from "../lib/formatar";
import { toast } from "../toast";
import type { CompraCartao, ItemMes, PlanoMesInput, Transacao, TransacaoInput } from "../types";

type Edicao =
  | { tipo: "transacao"; inicial: TransacaoInput; editando: Transacao | null }
  | { tipo: "compra"; editando: CompraCartao | null }
  | { tipo: "plano" }
  | { tipo: "apagar"; item: ItemMes };

interface AcoesItem {
  editar: (i: ItemMes) => void;
  apagar: (i: ItemMes) => void;
  lancar: (i: ItemMes) => void;
  encerrar: (i: ItemMes) => void;
}

function repete(i: ItemMes): boolean {
  return i.origem !== "compra" && (i.recorrencia === "mensal" || i.recorrencia === "parcelado");
}

function mesAnterior(mes: number, ano: number) {
  return mes === 1 ? { mes: 12, ano: ano - 1 } : { mes: mes - 1, ano };
}

export default function Mes() {
  const { mes, ano, setPeriodo } = usePeriodo();
  const [edicao, setEdicao] = useState<Edicao | null>(null);
  const resumo = useCarregar(() => mesApi.resumo(mes, ano), [mes, ano]);
  const cartoes = useCarregar(cartoesApi.listar, []);
  const m = resumo.dados;

  function fechar() {
    setEdicao(null);
  }
  function salvou() {
    setEdicao(null);
    resumo.recarregar();
  }

  async function editar(item: ItemMes) {
    if (item.id === null) return;
    if (item.origem === "transacao") {
      const t = await transacoesApi.obter(item.id);
      setEdicao({ tipo: "transacao", inicial: transacaoParaInput(t), editando: t });
    } else {
      const compra = (await cartoesApi.listarCompras()).find((c) => c.id === item.id) ?? null;
      setEdicao({ tipo: "compra", editando: compra });
    }
  }

  async function apagar(item: ItemMes) {
    if (item.id === null) return;
    if (repete(item)) {
      setEdicao({ tipo: "apagar", item });
      return;
    }
    const aviso =
      item.origem === "compra"
        ? `Apagar a compra "${item.descricao}" do cartão? Some de todas as faturas.`
        : `Apagar "${item.descricao}" deste mês?`;
    if (!confirm(aviso)) return;
    try {
      if (item.origem === "compra") await cartoesApi.removerCompra(item.id);
      else await transacoesApi.remover(item.id);
    } catch {
      return;
    }
    resumo.recarregar();
  }

  async function encerrar(item: ItemMes) {
    if (
      !confirm(
        `Parar de repetir "${item.descricao}" a partir de ${NOMES_MESES[mes - 1]}/${ano}?\n\n` +
          "Os lançamentos futuros ainda não pagos serão apagados.",
      )
    )
      return;
    const ultimo = mesAnterior(mes, ano);
    const { removidos } = await transacoesApi.encerrarRecorrencia(
      item.descricao,
      item.categoria,
      ultimo.mes,
      ultimo.ano,
    );
    toast.sucesso(
      `"${item.descricao}" não se repete mais a partir de ${NOMES_MESES[mes - 1]}/${ano}.` +
        (removidos
          ? ` ${plural(removidos, "lançamento futuro não pago removido", "lançamentos futuros não pagos removidos")}.`
          : ""),
    );
    salvou();
  }

  async function lancar(item: ItemMes) {
    if (item.molde_id === null) return;
    const molde = await transacoesApi.obter(item.molde_id);
    const [atual] = item.quantidade.includes("/") ? item.quantidade.split("/").map(Number) : [null];
    const dia = String(item.dia ?? 1).padStart(2, "0");
    setEdicao({
      tipo: "transacao",
      editando: null,
      inicial: {
        ...transacaoParaInput(molde),
        data: `${ano}-${String(mes).padStart(2, "0")}-${dia}`,
        situacao: "nao_iniciada",
        observacao: null,
        parcela_atual: atual,
        parcelas_total: atual ? molde.parcelas_total : null,
      },
    });
  }

  const acoes: AcoesItem = { editar, apagar, lancar, encerrar };

  async function alternarPago(item: ItemMes) {
    if (item.id === null || item.origem !== "transacao") return;
    const situacao = item.situacao === "concluido" ? "nao_iniciada" : "concluido";
    try {
      await transacoesApi.atualizar(item.id, { situacao });
    } finally {
      resumo.recarregar();
    }
  }

  async function lancarPrevistos() {
    const criadas = await transacoesApi.gerarRecorrentes(mes, ano);
    toast.sucesso(
      `${plural(criadas.length, "lançamento criado", "lançamentos criados")} em ${NOMES_MESES[mes - 1]}.`,
    );
    resumo.recarregar();
  }

  const listaCartoes = cartoes.dados ?? [];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted">Planejamento do mês</p>
          <h1 className="text-2xl font-semibold tracking-tight">
            {NOMES_MESES[mes - 1]} {ano}
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <SeletorMes mes={mes} ano={ano} aoMudar={setPeriodo} />
          <button className="btn-ghost flex items-center gap-2" onClick={() => setEdicao({ tipo: "plano" })}>
            <NotebookPen className="h-4 w-4" /> Plano do mês
          </button>
        </div>
      </header>

      {!m ? (
        <p className="text-muted">{resumo.erro ? "Não foi possível carregar o mês." : "Carregando…"}</p>
      ) : (
        <>
          {m.previstos > 0 && (
            <div className="card py-3! flex flex-wrap items-center justify-between gap-3 border-accent/30">
              <p className="text-sm text-gray-300">
                {m.previstos === 1
                  ? "1 lançamento que se repete ainda não foi criado neste mês"
                  : `${m.previstos} lançamentos que se repetem ainda não foram criados neste mês`}{" "}
                — aparecem como <span className="badge bg-white/5 text-muted">previsto</span>.
              </p>
              <BotaoAcao className="btn-ghost flex items-center gap-2 text-sm" acao={lancarPrevistos}>
                <RefreshCw className="h-4 w-4" /> Lançar todos agora
              </BotaoAcao>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <Card
              titulo="Gasto fixo do mês"
              valor={formatarReal(m.gasto_fixo)}
              cor="muted"
              legenda={`Pix/boleto ${formatarReal(m.fixo_conta)} · Cartão ${formatarReal(m.fixo_cartao)}`}
            />
            <Card
              titulo="Sobra da 1ª entrada"
              valor={m.sobra_primeira_entrada !== null ? formatarReal(m.sobra_primeira_entrada) : "—"}
              cor={(m.sobra_primeira_entrada ?? 0) < 0 ? "danger" : "success"}
              legenda={
                m.primeira_entrada
                  ? `${m.primeira_entrada.descricao}: ${formatarReal(m.primeira_entrada.valor ?? 0)} cobre os fixos e sobra isso`
                  : "Nenhuma entrada cadastrada no mês"
              }
            />
            <CardMeta
              descricao={m.plano.meta_descricao}
              valor={m.plano.meta_valor}
              dividas={m.total_dividas}
              aoDefinir={() => setEdicao({ tipo: "plano" })}
            />
            <CardLimite
              usado={m.cartao_variavel}
              limite={m.plano.limite_cartao}
              aoDefinir={() => setEdicao({ tipo: "plano" })}
            />
          </div>

          <Secao
            titulo="Receitas"
            total={m.total_receitas}
            acao={
              <BotaoNovo
                onClick={() =>
                  setEdicao({
                    tipo: "transacao",
                    inicial: novaTransacao({
                      tipo: "receita",
                      categoria: "salario",
                      situacao: "nao_iniciada",
                      data: dataPadrao(mes, ano),
                    }),
                    editando: null,
                  })
                }
              >
                Receita
              </BotaoNovo>
            }
          >
            <TabelaItens
              itens={[...m.receitas, ...m.beneficios]}
              vazio="Nenhuma receita neste mês."
              acoes={acoes}
              mostrarQuantidade={false}
            />
            {m.total_beneficios > 0 && (
              <p className="text-xs text-muted px-4 pb-3">
                Benefícios (voucher) somam {formatarReal(m.total_beneficios)} e não entram no saldo da conta.
              </p>
            )}
          </Secao>

          <Secao
            titulo="Despesas fixas"
            total={m.gasto_fixo}
            subtitulo="Contas que se repetem + assinaturas e parcelas do cartão (fatura que vence no mês)"
            acao={
              <div className="flex gap-2">
                <BotaoNovo
                  onClick={() =>
                    setEdicao({
                      tipo: "transacao",
                      inicial: novaTransacao({
                        tipo: "despesa",
                        recorrencia: "mensal",
                        situacao: "nao_iniciada",
                        data: dataPadrao(mes, ano),
                      }),
                      editando: null,
                    })
                  }
                >
                  Conta
                </BotaoNovo>
                {listaCartoes.length > 0 && (
                  <BotaoNovo onClick={() => setEdicao({ tipo: "compra", editando: null })}>
                    <CreditCard className="h-3.5 w-3.5" /> No cartão
                  </BotaoNovo>
                )}
              </div>
            }
          >
            <TabelaItens itens={m.fixos} vazio="Nenhuma despesa fixa neste mês." acoes={acoes} />
            {m.cartao_variavel > 0 && (
              <p className="text-xs text-muted px-4 pb-3">
                Fora isso, a fatura do mês tem {formatarReal(m.cartao_variavel)} em compras do dia a dia (veja
                em Cartões).
              </p>
            )}
          </Secao>

          <Secao
            titulo="Outras saídas do mês"
            total={m.outras_despesas}
            subtitulo="Despesas eventuais e investimentos (não entram no gasto fixo)"
            acao={
              <BotaoNovo
                onClick={() =>
                  setEdicao({
                    tipo: "transacao",
                    inicial: novaTransacao({
                      tipo: "despesa",
                      recorrencia: "eventual",
                      situacao: "nao_iniciada",
                      data: dataPadrao(mes, ano),
                    }),
                    editando: null,
                  })
                }
              >
                Despesa
              </BotaoNovo>
            }
          >
            <TabelaItens itens={m.outras} vazio="Nenhuma despesa eventual neste mês." acoes={acoes} />
          </Secao>

          <Secao
            titulo="Dívidas do mês"
            total={m.total_dividas}
            subtitulo="Marque quando pagar"
            acao={
              <BotaoNovo
                onClick={() =>
                  setEdicao({
                    tipo: "transacao",
                    inicial: novaTransacao({
                      tipo: "quitacao",
                      categoria: "quitacao",
                      situacao: "nao_iniciada",
                      data: dataPadrao(mes, ano),
                    }),
                    editando: null,
                  })
                }
              >
                Pagamento
              </BotaoNovo>
            }
          >
            {m.dividas.length === 0 ? (
              <p className="text-sm text-muted text-center py-6">Nenhum pagamento de dívida neste mês.</p>
            ) : (
              <ul className="divide-y divide-white/5">
                {m.dividas.map((d, i) => (
                  <li key={d.id ?? `p${i}`} className="flex items-center gap-3 px-4 py-2.5">
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-accent"
                      checked={d.situacao === "concluido"}
                      disabled={d.id === null}
                      onChange={() => alternarPago(d)}
                      aria-label={`Marcar ${d.descricao} como pago`}
                    />
                    <span className="w-16 text-sm text-muted">{d.dia ? `dia ${d.dia}` : ""}</span>
                    <span
                      className={["flex-1", d.situacao === "concluido" ? "line-through text-muted" : ""].join(
                        " ",
                      )}
                    >
                      {d.descricao}
                      {d.observacao && <span className="text-xs text-muted ml-2">{d.observacao}</span>}
                    </span>
                    <span className="tabular-nums">{formatarReal(d.valor ?? 0)}</span>
                    <Acoes item={d} acoes={acoes} />
                  </li>
                ))}
              </ul>
            )}
          </Secao>

          <div className="card">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">Anotações do mês</h3>
              <button className="btn-ghost text-sm" onClick={() => setEdicao({ tipo: "plano" })}>
                Editar
              </button>
            </div>
            {m.plano.anotacoes ? (
              <p className="text-sm text-gray-300 whitespace-pre-wrap">{m.plano.anotacoes}</p>
            ) : (
              <p className="text-sm text-muted">Nada anotado. Use para regras e lembretes do mês.</p>
            )}
            <p className="text-xs text-muted mt-4 pt-3 border-t border-white/5">
              Livre no mês: <span className="text-gray-200 font-medium">{formatarReal(m.livre)}</span> —
              entradas menos gasto fixo, outras saídas, dívidas do mês e compras do dia a dia já na fatura.
            </p>
          </div>
        </>
      )}

      {edicao?.tipo === "transacao" && (
        <ModalTransacao
          inicial={edicao.inicial}
          editando={edicao.editando}
          aoFechar={fechar}
          aoSalvar={salvou}
        />
      )}
      {edicao?.tipo === "compra" && listaCartoes.length > 0 && (
        <ModalCompra
          cartoes={listaCartoes}
          cartaoId={edicao.editando?.cartao_id ?? listaCartoes[0].id}
          mes={mes}
          ano={ano}
          editando={edicao.editando}
          padrao={{ recorrente: true }}
          aoFechar={fechar}
          aoSalvar={salvou}
        />
      )}
      {edicao?.tipo === "apagar" && (
        <ModalApagarRecorrente
          item={edicao.item}
          mes={mes}
          ano={ano}
          aoFechar={fechar}
          aoApagarSoEste={async () => {
            await transacoesApi.remover(edicao.item.id!);
            salvou();
          }}
          aoEncerrar={() => encerrar(edicao.item)}
        />
      )}
      {edicao?.tipo === "plano" && m && (
        <ModalPlano mes={mes} ano={ano} inicial={m.plano} aoFechar={fechar} aoSalvar={salvou} />
      )}
    </div>
  );
}

function Secao({
  titulo,
  subtitulo,
  total,
  acao,
  children,
}: {
  titulo: string;
  subtitulo?: string;
  total: number;
  acao: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="card p-0! overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-white/5">
        <div>
          <h3 className="font-semibold">
            {titulo} <span className="text-muted font-normal">· {formatarReal(total)}</span>
          </h3>
          {subtitulo && <p className="text-xs text-muted mt-0.5">{subtitulo}</p>}
        </div>
        {acao}
      </div>
      {children}
    </div>
  );
}

function BotaoNovo({ onClick, children }: { onClick: () => void; children: ReactNode }) {
  return (
    <button className="btn-ghost text-sm flex items-center gap-1.5 py-1.5!" onClick={onClick}>
      <Plus className="h-3.5 w-3.5" /> {children}
    </button>
  );
}

function BotaoIcone({
  titulo,
  onClick,
  perigo = false,
  children,
}: {
  titulo: string;
  onClick: () => void;
  perigo?: boolean;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      className={["p-1.5 rounded-sm", perigo ? "hover:bg-danger/20 text-danger" : "hover:bg-white/10"].join(
        " ",
      )}
      onClick={onClick}
      title={titulo}
      aria-label={titulo}
    >
      {children}
    </button>
  );
}

function Acoes({ item, acoes }: { item: ItemMes; acoes: AcoesItem }) {
  if (item.id === null) {
    return (
      <div className="flex gap-1 justify-end items-center">
        <span className="badge bg-white/5 text-muted mr-1" title="Ainda não lançado neste mês">
          previsto
        </span>
        <BotaoIcone titulo="Lançar neste mês" onClick={() => acoes.lancar(item)}>
          <Plus className="h-4 w-4" />
        </BotaoIcone>
        <BotaoIcone titulo="Parar de repetir a partir deste mês" onClick={() => acoes.encerrar(item)}>
          <CalendarX className="h-4 w-4" />
        </BotaoIcone>
      </div>
    );
  }
  return (
    <div className="flex gap-1 justify-end">
      <BotaoIcone titulo="Editar" onClick={() => acoes.editar(item)}>
        <Pencil className="h-4 w-4" />
      </BotaoIcone>
      <BotaoIcone titulo="Apagar" perigo onClick={() => acoes.apagar(item)}>
        <Trash2 className="h-4 w-4" />
      </BotaoIcone>
    </div>
  );
}

function TabelaItens({
  itens,
  vazio,
  acoes,
  mostrarQuantidade = true,
}: {
  itens: ItemMes[];
  vazio: string;
  acoes: AcoesItem;
  mostrarQuantidade?: boolean;
}) {
  const { rotulo } = useOpcoes();
  if (itens.length === 0) return <p className="text-sm text-muted text-center py-6">{vazio}</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm min-w-[720px]">
        <thead className="bg-white/5 text-xs text-muted">
          <tr>
            <th className="text-left px-4 py-2.5">Descrição</th>
            <th className="text-right px-4 py-2.5">Valor</th>
            {mostrarQuantidade && <th className="text-left px-4 py-2.5">Quantidade</th>}
            <th className="text-left px-4 py-2.5">Quando</th>
            <th className="text-left px-4 py-2.5">Meio</th>
            <th className="text-left px-4 py-2.5">Situação</th>
            <th className="px-4 py-2.5"></th>
          </tr>
        </thead>
        <tbody>
          {itens.map((item, i) => (
            <tr key={`${item.origem}-${item.id ?? i}`} className="border-t border-white/5 hover:bg-white/5">
              <td className="px-4 py-2.5">
                <p className="font-medium">
                  {item.descricao}
                  {item.tipo === "beneficio" && (
                    <span className="badge bg-white/5 text-muted ml-2">fora do saldo</span>
                  )}
                </p>
                <p className="text-xs text-muted">
                  {rotulo("categoria", item.categoria)}
                  {item.observacao && ` · ${item.observacao}`}
                </p>
              </td>
              <td className="px-4 py-2.5 text-right tabular-nums">
                {item.valor === null ? (
                  <span className="text-muted">sem valor</span>
                ) : (
                  formatarReal(item.valor)
                )}
              </td>
              {mostrarQuantidade && (
                <td className="px-4 py-2.5">
                  <span className="badge bg-white/5 text-gray-300">{item.quantidade}</span>
                </td>
              )}
              <td className="px-4 py-2.5 text-muted">{item.dia ? `dia ${item.dia}` : "—"}</td>
              <td className="px-4 py-2.5 text-muted">{item.meio ?? "—"}</td>
              <td className="px-4 py-2.5">
                {item.situacao && (
                  <span
                    className={[
                      "badge",
                      item.situacao === "concluido" ? "bg-success/15 text-success" : "bg-white/5 text-muted",
                    ].join(" ")}
                  >
                    {rotuloSituacao(item.situacao, item.tipo)}
                  </span>
                )}
              </td>
              <td className="px-4 py-2.5">
                <Acoes item={item} acoes={acoes} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CardMeta({
  descricao,
  valor,
  dividas,
  aoDefinir,
}: {
  descricao: string | null;
  valor: number | null;
  dividas: number;
  aoDefinir: () => void;
}) {
  if (valor === null) {
    return (
      <button type="button" onClick={aoDefinir} className="card text-left hover:border-accent/30 transition">
        <p className="text-sm text-muted">Meta do mês</p>
        <p className="mt-2 text-sm text-muted">Sem meta para este mês. Clique para definir.</p>
      </button>
    );
  }
  return (
    <Card
      titulo="Meta do mês"
      valor={formatarReal(valor)}
      cor="accent"
      legenda={`${descricao ?? "Meta"} · dívidas no mês: ${formatarReal(dividas)}`}
    />
  );
}

function CardLimite({
  usado,
  limite,
  aoDefinir,
}: {
  usado: number;
  limite: number | null;
  aoDefinir: () => void;
}) {
  if (limite === null) {
    return (
      <button type="button" onClick={aoDefinir} className="card text-left hover:border-accent/30 transition">
        <p className="text-sm text-muted">Cartão fora das fixas</p>
        <p className="mt-1.5 text-2xl font-semibold tracking-tight">{formatarReal(usado)}</p>
        <p className="mt-1 text-xs text-muted">Sem limite para este mês. Clique para definir.</p>
      </button>
    );
  }
  const passou = usado > limite;
  const pct = limite > 0 ? Math.min((usado / limite) * 100, 100) : 100;
  return (
    <div className="card">
      <p className="text-sm text-muted">Cartão fora das fixas</p>
      <p
        className={[
          "mt-1.5 text-2xl font-semibold tracking-tight",
          passou ? "text-danger" : "text-gray-100",
        ].join(" ")}
      >
        {formatarReal(usado)}
      </p>
      <div className="mt-2 h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div
          className={["h-full rounded-full", passou ? "bg-danger" : "bg-accent"].join(" ")}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-muted">
        Limite {formatarReal(limite)} ·{" "}
        {passou ? `passou ${formatarReal(usado - limite)}` : `restam ${formatarReal(limite - usado)}`}
      </p>
    </div>
  );
}

function ModalPlano({
  mes,
  ano,
  inicial,
  aoFechar,
  aoSalvar,
}: {
  mes: number;
  ano: number;
  inicial: PlanoMesInput & { salvo: boolean };
  aoFechar: () => void;
  aoSalvar: () => void;
}) {
  const [form, setForm] = useState<PlanoMesInput>({
    meta_descricao: inicial.meta_descricao,
    meta_valor: inicial.meta_valor,
    limite_cartao: inicial.limite_cartao,
    anotacoes: inicial.anotacoes,
  });

  async function copiarAnterior() {
    const anterior = mes === 1 ? { mes: 12, ano: ano - 1 } : { mes: mes - 1, ano };
    const { plano } = await mesApi.resumo(anterior.mes, anterior.ano);
    if (!plano.salvo) {
      toast.info(`${NOMES_MESES[anterior.mes - 1]} não tem plano salvo.`);
      return;
    }
    setForm({
      meta_descricao: plano.meta_descricao,
      meta_valor: plano.meta_valor,
      limite_cartao: plano.limite_cartao,
      anotacoes: plano.anotacoes,
    });
  }

  const numero = (v: string) => (v === "" ? null : Number(v));

  return (
    <ModalFormulario
      titulo={`Plano de ${NOMES_MESES[mes - 1]} ${ano}`}
      aoFechar={aoFechar}
      aoEnviar={async () => {
        await mesApi.salvarPlano(mes, ano, form);
        aoSalvar();
      }}
    >
      {!inicial.salvo && (
        <button type="button" className="btn-ghost text-sm w-full" onClick={copiarAnterior}>
          Copiar do mês anterior
        </button>
      )}
      <div className="grid grid-cols-3 gap-3">
        <label className="col-span-2">
          <span className="text-xs text-muted">Meta do mês</span>
          <input
            className="input w-full mt-1"
            value={form.meta_descricao ?? ""}
            onChange={(e) => setForm({ ...form, meta_descricao: e.target.value || null })}
            placeholder="Ex.: separar para as dívidas"
          />
        </label>
        <label>
          <span className="text-xs text-muted">Valor (R$)</span>
          <input
            className="input w-full mt-1"
            type="number"
            step="0.01"
            min={0}
            value={form.meta_valor ?? ""}
            onChange={(e) => setForm({ ...form, meta_valor: numero(e.target.value) })}
          />
        </label>
      </div>
      <label className="block">
        <span className="text-xs text-muted">Limite no cartão fora das fixas (R$)</span>
        <input
          className="input w-full mt-1"
          type="number"
          step="0.01"
          min={0}
          value={form.limite_cartao ?? ""}
          onChange={(e) => setForm({ ...form, limite_cartao: numero(e.target.value) })}
          placeholder="Deixe vazio para não ter limite"
        />
      </label>
      <label className="block">
        <span className="text-xs text-muted">Anotações (regras, lembretes, cofrinho…)</span>
        <textarea
          className="input w-full mt-1"
          rows={5}
          value={form.anotacoes ?? ""}
          onChange={(e) => setForm({ ...form, anotacoes: e.target.value || null })}
        />
      </label>
    </ModalFormulario>
  );
}

function ModalApagarRecorrente({
  item,
  mes,
  ano,
  aoFechar,
  aoApagarSoEste,
  aoEncerrar,
}: {
  item: ItemMes;
  mes: number;
  ano: number;
  aoFechar: () => void;
  aoApagarSoEste: () => Promise<void>;
  aoEncerrar: () => Promise<void>;
}) {
  const [escolha, setEscolha] = useState<"encerrar" | "so_este">("encerrar");
  const opcoes: { valor: "encerrar" | "so_este"; titulo: string; texto: string }[] = [
    {
      valor: "encerrar",
      titulo: `Parar de repetir a partir de ${NOMES_MESES[mes - 1]}/${ano}`,
      texto: "Some deste mês e dos próximos (lançamentos futuros já pagos são mantidos).",
    },
    {
      valor: "so_este",
      titulo: "Apagar só este lançamento",
      texto: "Os próximos meses continuam. Neste mês ele volta a aparecer como previsto.",
    },
  ];
  return (
    <ModalFormulario
      titulo={`Apagar "${item.descricao}"`}
      aoFechar={aoFechar}
      aoEnviar={escolha === "encerrar" ? aoEncerrar : aoApagarSoEste}
      textoSalvar="Apagar"
    >
      <p className="text-sm text-muted">Este lançamento se repete todo mês. O que você quer fazer?</p>
      <div className="space-y-2">
        {opcoes.map((o) => (
          <label
            key={o.valor}
            className={[
              "flex gap-3 rounded-lg px-3 py-2.5 cursor-pointer border",
              escolha === o.valor ? "border-accent/50 bg-accent/10" : "border-white/5 bg-white/5",
            ].join(" ")}
          >
            <input
              type="radio"
              name="escolha"
              className="mt-1 accent-accent"
              checked={escolha === o.valor}
              onChange={() => setEscolha(o.valor)}
            />
            <span>
              <span className="block text-sm font-medium">{o.titulo}</span>
              <span className="block text-xs text-muted">{o.texto}</span>
            </span>
          </label>
        ))}
      </div>
    </ModalFormulario>
  );
}
