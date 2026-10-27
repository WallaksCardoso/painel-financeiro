import { Check, CheckCircle2, CreditCard, Pencil, Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import BotaoAcao from "../components/BotaoAcao";
import { cartoesApi } from "../api";
import { usePeriodo } from "../contexts/Periodo";
import ModalCompra from "../components/formularios/ModalCompra";
import ModalFormulario from "../components/Modal";
import SeletorMes from "../components/SeletorMes";
import { useOpcoes } from "../contexts/Opcoes";
import { useCarregar } from "../hooks/useCarregar";
import { hojeISO } from "../lib/datas";
import { NOMES_MESES } from "../lib/constantes";
import { formatarData, formatarReal, plural } from "../lib/formatar";
import { type Cartao, type CartaoInput, type CompraCartao } from "../types";

const CORES_CARTAO = ["#1b7f8f", "#2f9e76", "#7584df", "#b08a2e", "#c25b5e", "#8a6fc0", "#b86a3c", "#5b6470"];

type FiltroFatura = "todas" | "fixas" | "variaveis";

const CARTAO_VAZIO: CartaoInput = {
  nome: "",
  bandeira: null,
  limite: 0,
  dia_fechamento: 1,
  dia_vencimento: 10,
  cor: CORES_CARTAO[0],
  ativo: true,
};

export default function Cartoes() {
  const { rotulo } = useOpcoes();
  const { mes, ano, setPeriodo } = usePeriodo();
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [filtro, setFiltro] = useState<FiltroFatura>("todas");

  const [criandoCartao, setCriandoCartao] = useState(false);
  const [editandoCartao, setEditandoCartao] = useState<Cartao | null>(null);
  const [criandoCompra, setCriandoCompra] = useState(false);
  const [editandoCompra, setEditandoCompra] = useState<CompraCartao | null>(null);
  const [pagandoFatura, setPagandoFatura] = useState(false);

  const cartoesCarga = useCarregar(cartoesApi.listar, []);
  const cartoes = cartoesCarga.dados ?? [];
  const cartaoAtual = cartoes.find((c) => c.id === escolhido) ?? cartoes[0] ?? null;
  const cartaoId = cartaoAtual?.id ?? null;

  const comprasCarga = useCarregar(
    () => (cartaoId === null ? Promise.resolve([]) : cartoesApi.listarCompras(cartaoId)),
    [cartaoId],
  );
  const compras = comprasCarga.dados ?? [];

  const faturaCarga = useCarregar(
    () => (cartaoId === null ? Promise.resolve(null) : cartoesApi.faturaQueVence(cartaoId, mes, ano)),
    [cartaoId, mes, ano],
  );
  const fatura = faturaCarga.dados;

  function recarregarCompraEFatura() {
    comprasCarga.recarregar();
    faturaCarga.recarregar();
  }

  const itensFiltrados = useMemo(() => {
    if (!fatura) return [];
    const fixa = (i: (typeof fatura.itens)[number]) => i.recorrente || i.parcelas_total > 1;
    if (filtro === "fixas") return fatura.itens.filter(fixa);
    if (filtro === "variaveis") return fatura.itens.filter((i) => !fixa(i));
    return fatura.itens;
  }, [fatura, filtro]);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Cartões</h1>
          <p className="text-sm text-muted mt-1">Acompanhe limites, faturas e compras parceladas</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setCriandoCartao(true)}>
          <Plus className="h-4 w-4" /> Novo cartão
        </button>
      </header>

      {cartoes.length === 0 ? (
        <div className="card text-center py-16">
          <CreditCard className="h-12 w-12 text-muted mx-auto mb-3" />
          <p className="text-muted">Nenhum cartão cadastrado ainda. Comece adicionando o primeiro.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cartoes.map((c) => (
            <CartaoCard
              key={c.id}
              cartao={c}
              ativo={c.id === cartaoId}
              aoSelecionar={() => setEscolhido(c.id)}
              aoEditar={() => setEditandoCartao(c)}
              aoRemover={async () => {
                if (confirm(`Apagar cartão "${c.nome}"? Todas as compras também serão removidas.`)) {
                  await cartoesApi.remover(c.id).catch(() => undefined);
                  cartoesCarga.recarregar();
                }
              }}
            />
          ))}
        </div>
      )}

      {cartaoAtual && fatura && (
        <>
          <div className="card">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
              <div>
                <p className="text-xs text-muted">Fatura — {cartaoAtual.nome}</p>
                <div className="flex items-center gap-3 mt-1">
                  <p className="text-2xl font-semibold tracking-tight">{formatarReal(fatura.total)}</p>
                  {fatura.pago && (
                    <span className="badge bg-success/15 text-success flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Paga em {formatarData(fatura.pago_em!)}
                    </span>
                  )}
                  {fatura.pago &&
                    fatura.valor_pago !== null &&
                    Math.abs(fatura.valor_pago - fatura.total) >= 0.01 && (
                      <span
                        className="badge bg-warning/15 text-warning"
                        title="O valor marcado como pago é diferente do total da fatura no painel"
                      >
                        Pago {formatarReal(fatura.valor_pago)} · diferença de{" "}
                        {formatarReal(Math.abs(fatura.valor_pago - fatura.total))}
                      </span>
                    )}
                </div>
                <p className="text-xs text-muted mt-1">
                  Vence em {formatarData(fatura.vencimento)} · fecha em{" "}
                  {NOMES_MESES[fatura.mes - 1].toLowerCase()}/{fatura.ano} ·{" "}
                  {plural(fatura.itens.length, "item", "itens")}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted">Fatura que vence em</span>
                <SeletorMes mes={mes} ano={ano} aoMudar={setPeriodo} />
                {fatura.pago ? (
                  <BotaoAcao
                    className="btn-ghost flex items-center gap-2"
                    acao={async () => {
                      if (fatura.fatura_paga_id !== null && confirm("Desmarcar pagamento dessa fatura?")) {
                        await cartoesApi.desmarcarFaturaPaga(fatura.fatura_paga_id);
                        faturaCarga.recarregar();
                      }
                    }}
                  >
                    Desmarcar pagamento
                  </BotaoAcao>
                ) : (
                  fatura.itens.length > 0 && (
                    <button
                      className="rounded-lg bg-success/90 hover:bg-success text-bg font-semibold px-4 py-2 transition flex items-center gap-2"
                      onClick={() => setPagandoFatura(true)}
                    >
                      <Check className="h-4 w-4" /> Marcar como paga
                    </button>
                  )
                )}
                <button
                  className="btn-primary flex items-center gap-2"
                  onClick={() => setCriandoCompra(true)}
                >
                  <Plus className="h-4 w-4" /> Nova compra
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
              <MiniBox
                titulo="Fixos"
                valor={fatura.total_fixo}
                cor="text-gray-100"
                legenda="Assinaturas e parcelas"
              />
              <MiniBox
                titulo="Do dia a dia"
                valor={fatura.total_variavel}
                cor="text-gray-100"
                legenda="Compras à vista"
              />
              <MiniBox
                titulo="Comprometido futuro"
                valor={fatura.total_comprometido_futuro}
                cor="text-gray-100"
                legenda="Soma de parcelas que ainda virão"
              />
            </div>

            <div className="flex gap-2 mb-3 text-sm">
              <FiltroBtn ativo={filtro === "todas"} onClick={() => setFiltro("todas")}>
                Todas
              </FiltroBtn>
              <FiltroBtn ativo={filtro === "fixas"} onClick={() => setFiltro("fixas")}>
                Só fixas
              </FiltroBtn>
              <FiltroBtn ativo={filtro === "variaveis"} onClick={() => setFiltro("variaveis")}>
                Só do dia a dia
              </FiltroBtn>
            </div>

            {itensFiltrados.length === 0 ? (
              <p className="text-muted text-sm py-6 text-center">
                Sem lançamentos {filtro !== "todas" ? "deste tipo" : "nesta fatura"}.
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead className="text-xs text-muted">
                  <tr>
                    <th className="text-left pb-2">Compra</th>
                    <th className="text-left pb-2">Categoria</th>
                    <th className="text-left pb-2">Tags</th>
                    <th className="text-left pb-2">Parcela</th>
                    <th className="text-right pb-2">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {itensFiltrados.map((item) => (
                    <tr key={`${item.compra_id}-${item.parcela_atual}`} className="border-t border-white/5">
                      <td className="py-2.5">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{item.descricao}</span>
                          {item.recorrente && (
                            <span className="badge bg-warning/15 text-warning">Assinatura</span>
                          )}
                        </div>
                      </td>
                      <td className="py-2.5 text-muted">{rotulo("categoria", item.categoria)}</td>
                      <td className="py-2.5">
                        <div className="flex flex-wrap gap-1">
                          {item.tags.map((t) => (
                            <span key={t} className="badge bg-white/5 text-gray-300">
                              #{t}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-2.5 text-muted">
                        {item.parcelas_total > 1 ? (
                          <>
                            {item.parcela_atual}/{item.parcelas_total}
                            {item.parcelas_restantes > 0 && (
                              <span className="text-xs ml-2 opacity-70">
                                (faltam {item.parcelas_restantes})
                              </span>
                            )}
                          </>
                        ) : item.recorrente ? (
                          "Mensal"
                        ) : (
                          "À vista"
                        )}
                      </td>
                      <td className="py-2.5 text-right tabular-nums">
                        {item.recorrente && item.valor_parcela === 0 ? (
                          <span className="text-muted">sem valor</span>
                        ) : (
                          formatarReal(item.valor_parcela)
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="card p-0! overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-white/5">
              <h3 className="font-semibold">Todas as compras de {cartaoAtual.nome}</h3>
              <span className="text-xs text-muted">{plural(compras.length, "compra")}</span>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-white/5 text-xs text-muted">
                <tr>
                  <th className="text-left px-4 py-3">Descrição</th>
                  <th className="text-left px-4 py-3">Categoria</th>
                  <th className="text-left px-4 py-3">Tags</th>
                  <th className="text-left px-4 py-3">Data</th>
                  <th className="text-right px-4 py-3">Valor total</th>
                  <th className="text-right px-4 py-3">Parcelas</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {compras.length === 0 && (
                  <tr>
                    <td colSpan={7} className="text-center text-muted py-8">
                      Nenhuma compra registrada neste cartão.
                    </td>
                  </tr>
                )}
                {compras.map((c) => (
                  <tr key={c.id} className="border-t border-white/5 hover:bg-white/5">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{c.descricao}</span>
                        {c.recorrente && <span className="badge bg-warning/15 text-warning">Assinatura</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted">{rotulo("categoria", c.categoria)}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {c.tags.map((t) => (
                          <span key={t} className="badge bg-white/5 text-gray-300">
                            #{t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted">{formatarData(c.data_compra)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {c.recorrente && c.valor_total === 0 ? (
                        <span className="text-muted">sem valor</span>
                      ) : (
                        formatarReal(c.valor_total)
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-muted">
                      {c.recorrente
                        ? "Mensal"
                        : c.parcelas > 1
                          ? `${c.parcelas}× ${formatarReal(c.valor_parcela)}`
                          : "À vista"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 justify-end">
                        <button
                          className="p-1.5 rounded-sm hover:bg-white/10"
                          onClick={() => setEditandoCompra(c)}
                          title="Editar"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          className="p-1.5 rounded-sm hover:bg-danger/20 text-danger"
                          onClick={async () => {
                            if (confirm(`Apagar "${c.descricao}"?`)) {
                              await cartoesApi.removerCompra(c.id).catch(() => undefined);
                              recarregarCompraEFatura();
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
        </>
      )}

      {pagandoFatura && cartaoAtual && fatura && (
        <ModalPagarFatura
          total={fatura.total}
          fechamento={dataFechamento(cartaoAtual.dia_fechamento, fatura.mes, fatura.ano)}
          aoFechar={() => setPagandoFatura(false)}
          aoEnviar={async (pago_em, valor_pago) => {
            await cartoesApi.marcarFaturaPaga(cartaoAtual.id, {
              mes: fatura.mes,
              ano: fatura.ano,
              pago_em,
              valor_pago,
            });
            setPagandoFatura(false);
            faturaCarga.recarregar();
          }}
        />
      )}

      {(criandoCartao || editandoCartao) && (
        <ModalCartao
          inicial={editandoCartao ? toCartaoInput(editandoCartao) : CARTAO_VAZIO}
          editando={editandoCartao}
          aoFechar={() => {
            setCriandoCartao(false);
            setEditandoCartao(null);
          }}
          aoSalvar={() => {
            setCriandoCartao(false);
            setEditandoCartao(null);
            cartoesCarga.recarregar();
          }}
        />
      )}

      {(criandoCompra || editandoCompra) && cartaoAtual && (
        <ModalCompra
          cartoes={cartoes}
          cartaoId={cartaoAtual.id}
          mes={mes}
          ano={ano}
          editando={editandoCompra}
          aoFechar={() => {
            setCriandoCompra(false);
            setEditandoCompra(null);
          }}
          aoSalvar={() => {
            setCriandoCompra(false);
            setEditandoCompra(null);
            recarregarCompraEFatura();
          }}
        />
      )}
    </div>
  );
}

function MiniBox({
  titulo,
  valor,
  cor,
  legenda,
}: {
  titulo: string;
  valor: number;
  cor: string;
  legenda?: string;
}) {
  return (
    <div className="rounded-md border border-white/[0.07] p-3">
      <p className="text-xs text-muted">{titulo}</p>
      <p className={["text-lg font-semibold mt-1", cor].join(" ")}>{formatarReal(valor)}</p>
      {legenda && <p className="text-[11px] text-muted mt-0.5">{legenda}</p>}
    </div>
  );
}

function FiltroBtn({
  ativo,
  onClick,
  children,
}: {
  ativo: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "px-3 py-1.5 rounded-lg transition text-sm",
        ativo ? "bg-white/[0.08] text-gray-100" : "bg-white/5 text-gray-300 hover:bg-white/10",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function toCartaoInput(c: Cartao): CartaoInput {
  return {
    nome: c.nome,
    bandeira: c.bandeira,
    limite: c.limite,
    dia_fechamento: c.dia_fechamento,
    dia_vencimento: c.dia_vencimento,
    cor: c.cor,
    ativo: c.ativo,
  };
}

interface CartaoCardProps {
  cartao: Cartao;
  ativo: boolean;
  aoSelecionar: () => void;
  aoEditar: () => void;
  aoRemover: () => void;
}

function CartaoCard({ cartao, ativo, aoSelecionar, aoEditar, aoRemover }: CartaoCardProps) {
  return (
    <button
      type="button"
      onClick={aoSelecionar}
      className={[
        "relative text-left rounded-lg p-5 pl-6 bg-bg-card border transition-colors overflow-hidden",
        ativo ? "border-accent" : "border-white/[0.07] hover:border-white/15",
      ].join(" ")}
    >
      <span className="absolute inset-y-0 left-0 w-1" style={{ backgroundColor: cartao.cor }} />
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-muted">{cartao.bandeira ?? "Cartão"}</p>
          <p className="text-base font-semibold mt-0.5">{cartao.nome}</p>
        </div>
      </div>
      <div className="mt-6 text-xs text-muted space-y-1">
        <p>Limite: {formatarReal(cartao.limite)}</p>
        <p>
          Fecha dia {cartao.dia_fechamento} · Vence dia {cartao.dia_vencimento}
        </p>
      </div>
      <div className="absolute bottom-2 right-3 flex gap-1">
        <span
          role="button"
          tabIndex={0}
          onClick={(e) => {
            e.stopPropagation();
            aoEditar();
          }}
          className="p-1.5 rounded-sm text-muted hover:bg-white/10 hover:text-gray-100 cursor-pointer"
          title="Editar"
        >
          <Pencil className="h-3.5 w-3.5" />
        </span>
        <span
          role="button"
          tabIndex={0}
          onClick={(e) => {
            e.stopPropagation();
            aoRemover();
          }}
          className="p-1.5 rounded-sm text-muted hover:bg-danger/20 hover:text-danger cursor-pointer"
          title="Apagar"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </span>
      </div>
    </button>
  );
}

function ModalCartao({
  inicial,
  editando,
  aoFechar,
  aoSalvar,
}: {
  inicial: CartaoInput;
  editando: Cartao | null;
  aoFechar: () => void;
  aoSalvar: () => void;
}) {
  const [form, setForm] = useState<CartaoInput>(inicial);

  function update<K extends keyof CartaoInput>(campo: K, valor: CartaoInput[K]) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  async function salvar() {
    if (editando) {
      await cartoesApi.atualizar(editando.id, form);
    } else {
      await cartoesApi.criar(form);
    }
    aoSalvar();
  }

  return (
    <ModalFormulario
      titulo={editando ? "Editar cartão" : "Novo cartão"}
      aoFechar={aoFechar}
      aoEnviar={salvar}
      textoSalvar={editando ? "Salvar" : "Criar"}
    >
      <div className="grid grid-cols-2 gap-3">
        <label className="col-span-2">
          <span className="text-xs text-muted">Nome</span>
          <input
            className="input w-full mt-1"
            required
            value={form.nome}
            onChange={(e) => update("nome", e.target.value)}
            placeholder="Ex.: Nubank, Inter, C6"
          />
        </label>
        <label>
          <span className="text-xs text-muted">Bandeira</span>
          <input
            className="input w-full mt-1"
            value={form.bandeira ?? ""}
            onChange={(e) => update("bandeira", e.target.value || null)}
            placeholder="Visa, Mastercard…"
          />
        </label>
        <label>
          <span className="text-xs text-muted">Limite (R$)</span>
          <input
            className="input w-full mt-1"
            type="number"
            step="0.01"
            value={form.limite}
            onChange={(e) => update("limite", Number(e.target.value))}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Dia de fechamento</span>
          <input
            className="input w-full mt-1"
            type="number"
            min={1}
            max={31}
            value={form.dia_fechamento}
            onChange={(e) => update("dia_fechamento", Number(e.target.value))}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Dia de vencimento</span>
          <input
            className="input w-full mt-1"
            type="number"
            min={1}
            max={31}
            value={form.dia_vencimento}
            onChange={(e) => update("dia_vencimento", Number(e.target.value))}
          />
        </label>
        <div className="col-span-2">
          <span className="text-xs text-muted">Cor</span>
          <div className="flex gap-2 mt-2 flex-wrap">
            {CORES_CARTAO.map((cor) => (
              <button
                key={cor}
                type="button"
                onClick={() => update("cor", cor)}
                aria-label={`Cor ${cor}`}
                aria-pressed={form.cor === cor}
                className={[
                  "h-9 w-9 rounded-full transition",
                  form.cor === cor ? "ring-2 ring-white" : "opacity-70 hover:opacity-100",
                ].join(" ")}
                style={{ background: cor }}
              />
            ))}
          </div>
        </div>
      </div>
    </ModalFormulario>
  );
}

function dataFechamento(dia: number, mes: number, ano: number): string {
  const ultimo = new Date(ano, mes, 0).getDate();
  return `${ano}-${String(mes).padStart(2, "0")}-${String(Math.min(dia, ultimo)).padStart(2, "0")}`;
}

function ModalPagarFatura({
  total,
  fechamento,
  aoFechar,
  aoEnviar,
}: {
  total: number;
  fechamento: string;
  aoFechar: () => void;
  aoEnviar: (pagoEm: string, valorPago: number) => Promise<void>;
}) {
  const [pagoEm, setPagoEm] = useState(hojeISO());
  const [valor, setValor] = useState(total);
  const diferente = Math.abs(valor - total) >= 0.01;
  return (
    <ModalFormulario
      titulo="Marcar fatura como paga"
      aoFechar={aoFechar}
      aoEnviar={() => aoEnviar(pagoEm, valor)}
      textoSalvar="Marcar como paga"
    >
      <div className="grid grid-cols-2 gap-3">
        <label>
          <span className="text-xs text-muted">Data do pagamento</span>
          <input
            className="input w-full mt-1"
            type="date"
            required
            value={pagoEm}
            onChange={(e) => setPagoEm(e.target.value)}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Valor pago (R$)</span>
          <input
            className="input w-full mt-1"
            type="number"
            step="0.01"
            min={0.01}
            required
            value={valor || ""}
            onChange={(e) => setValor(Number(e.target.value))}
          />
        </label>
      </div>
      <p className="text-xs text-muted">Total da fatura no painel: {formatarReal(total)}</p>
      {fechamento > hojeISO() && (
        <p className="text-xs text-warning">
          Atenção: essa fatura só fecha em {formatarData(fechamento)}. Compras feitas até lá ainda podem
          entrar nela.
        </p>
      )}
      {diferente && valor > 0 && (
        <p className="text-xs text-warning">
          O valor pago é {valor > total ? "maior" : "menor"} que o total da fatura (diferença de{" "}
          {formatarReal(Math.abs(valor - total))}). Confira se falta lançar alguma compra.
        </p>
      )}
    </ModalFormulario>
  );
}
