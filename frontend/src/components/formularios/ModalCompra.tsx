import { useState } from "react";
import { cartoesApi } from "../../api";
import { useOpcoes } from "../../contexts/Opcoes";
import { NOMES_MESES } from "../../lib/constantes";
import { dataPadrao } from "../../lib/datas";
import { formatarReal } from "../../lib/formatar";
import { toast } from "../../toast";
import type { Cartao, CompraCartao, CompraCartaoInput } from "../../types";
import ModalFormulario from "../Modal";

type ModoCompra = "nova" | "andamento";

const MODOS: [ModoCompra, string][] = [
  ["nova", "Valor total e data"],
  ["andamento", "Parcela atual (ex.: 10/12)"],
];

interface ValoresEmAndamento {
  valorParcela: number;
  parcelaAtual: number;
  parcelasTotal: number;
}

function compraParaInput(c: CompraCartao): CompraCartaoInput {
  return {
    cartao_id: c.cartao_id,
    descricao: c.descricao,
    valor_total: c.valor_total,
    data_compra: c.data_compra,
    parcelas: c.parcelas,
    categoria: c.categoria,
    recorrente: c.recorrente,
    tags: c.tags,
    observacao: c.observacao,
  };
}

function fechamentoDaFaturaQueVence(cartao: Cartao | undefined, mes: number, ano: number) {
  if (cartao && cartao.dia_vencimento <= cartao.dia_fechamento) {
    return mes === 1 ? { mes: 12, ano: ano - 1 } : { mes: mes - 1, ano };
  }
  return { mes, ano };
}

function parcelaNoMes(compra: CompraCartao, cartao: Cartao | undefined, mes: number, ano: number) {
  const f = fechamentoDaFaturaQueVence(cartao, mes, ano);
  const n = (f.ano - compra.primeira_fatura_ano) * 12 + (f.mes - compra.primeira_fatura_mes) + 1;
  return Math.min(Math.max(n, 1), compra.parcelas);
}

interface Props {
  cartoes: Cartao[];
  cartaoId: number;
  mes: number;
  ano: number;
  editando: CompraCartao | null;
  padrao?: Partial<CompraCartaoInput>;
  aoFechar: () => void;
  aoSalvar: () => void;
}

export default function ModalCompra({
  cartoes,
  cartaoId,
  mes,
  ano,
  editando,
  padrao,
  aoFechar,
  aoSalvar,
}: Props) {
  const { lista } = useOpcoes();
  const categorias = lista("categoria");
  const [form, setForm] = useState<CompraCartaoInput>(() =>
    editando
      ? compraParaInput(editando)
      : {
          cartao_id: cartaoId,
          descricao: "",
          valor_total: 0,
          data_compra: dataPadrao(mes, ano),
          parcelas: 1,
          categoria: "geral",
          recorrente: false,
          tags: [],
          observacao: null,
          ...padrao,
        },
  );
  const [tagsTexto, setTagsTexto] = useState(form.tags.join(", "));
  const [modo, setModo] = useState<ModoCompra>("nova");
  const cartaoAtual = cartoes.find((c) => c.id === form.cartao_id);
  const [andamento, setAndamento] = useState<ValoresEmAndamento>(() =>
    editando && editando.parcelas > 1
      ? {
          valorParcela: editando.valor_parcela,
          parcelaAtual: parcelaNoMes(editando, cartaoAtual, mes, ano),
          parcelasTotal: editando.parcelas,
        }
      : { valorParcela: 0, parcelaAtual: 1, parcelasTotal: 2 },
  );

  const categoria = categorias.some((c) => c.chave === form.categoria)
    ? form.categoria
    : (categorias[0]?.chave ?? form.categoria);

  function update<K extends keyof CompraCartaoInput>(campo: K, valor: CompraCartaoInput[K]) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  const [parcelasAntes, setParcelasAntes] = useState(form.parcelas);
  function marcarFixa(recorrente: boolean) {
    if (recorrente) setParcelasAntes(form.parcelas);
    setForm((f) => ({ ...f, recorrente, parcelas: recorrente ? 1 : parcelasAntes }));
  }

  async function salvar() {
    const tags = tagsTexto
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    let salva: CompraCartao;
    if (modo === "andamento") {
      const dados = {
        cartao_id: form.cartao_id,
        descricao: form.descricao,
        valor_parcela: andamento.valorParcela,
        parcela_atual: andamento.parcelaAtual,
        parcelas_total: andamento.parcelasTotal,
        mes,
        ano,
        vence_em: true,
        categoria,
        tags,
        observacao: form.observacao,
      };
      salva = editando
        ? await cartoesApi.atualizarCompraEmAndamento(editando.id, dados)
        : await cartoesApi.criarCompraEmAndamento(dados);
    } else if (editando) {
      salva = await cartoesApi.atualizarCompra(editando.id, { ...form, categoria, tags });
    } else {
      salva = await cartoesApi.criarCompra({ ...form, categoria, tags });
    }
    salva.avisos.forEach((aviso) => toast.info(aviso));
    aoSalvar();
  }

  const centavos = Math.round(form.valor_total * 100);
  const valorParcela = form.parcelas > 0 ? Math.floor(centavos / form.parcelas) / 100 : 0;
  const sobra = form.parcelas > 0 ? centavos % form.parcelas : 0;

  const seletorCategoria = (
    <label>
      <span className="text-xs text-muted">Categoria</span>
      <select
        className="input w-full mt-1"
        value={categoria}
        onChange={(e) => update("categoria", e.target.value)}
      >
        {categorias.map((c) => (
          <option key={c.chave} value={c.chave}>
            {c.nome}
          </option>
        ))}
      </select>
    </label>
  );

  const podeEmAndamento = !form.recorrente;

  return (
    <ModalFormulario
      titulo={editando ? "Editar compra no cartão" : "Nova compra no cartão"}
      aoFechar={aoFechar}
      aoEnviar={salvar}
      textoSalvar={editando ? "Salvar" : "Criar"}
    >
      {podeEmAndamento && (
        <div className="grid grid-cols-2 gap-1 rounded-lg bg-white/5 p-1 text-sm" role="tablist">
          {MODOS.map(([valor, rotulo]) => (
            <button
              key={valor}
              type="button"
              role="tab"
              aria-selected={modo === valor}
              onClick={() => setModo(valor)}
              className={[
                "rounded-md px-3 py-1.5 transition",
                modo === valor ? "bg-accent/20 text-accent-glow" : "text-gray-300 hover:bg-white/10",
              ].join(" ")}
            >
              {rotulo}
            </button>
          ))}
        </div>
      )}

      {cartoes.length > 1 && (
        <label className="block">
          <span className="text-xs text-muted">Cartão</span>
          <select
            className="input w-full mt-1"
            value={form.cartao_id}
            onChange={(e) => update("cartao_id", Number(e.target.value))}
          >
            {cartoes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
        </label>
      )}

      <label className="block">
        <span className="text-xs text-muted">Descrição</span>
        <input
          className="input w-full mt-1"
          required
          value={form.descricao}
          onChange={(e) => update("descricao", e.target.value)}
          placeholder="Ex.: Geladeira Magazine Luiza"
        />
      </label>

      {modo === "andamento" && podeEmAndamento ? (
        <div className="grid grid-cols-3 gap-3">
          <label>
            <span className="text-xs text-muted">Valor da parcela (R$)</span>
            <input
              className="input w-full mt-1"
              type="number"
              step="0.01"
              min={0.01}
              required
              value={andamento.valorParcela || ""}
              onChange={(e) => setAndamento({ ...andamento, valorParcela: Number(e.target.value) })}
            />
          </label>
          <label>
            <span className="text-xs text-muted">Parcela atual</span>
            <input
              className="input w-full mt-1"
              type="number"
              min={1}
              max={andamento.parcelasTotal}
              required
              value={andamento.parcelaAtual}
              onChange={(e) => setAndamento({ ...andamento, parcelaAtual: Number(e.target.value) })}
            />
          </label>
          <label>
            <span className="text-xs text-muted">De quantas</span>
            <input
              className="input w-full mt-1"
              type="number"
              min={1}
              max={60}
              required
              value={andamento.parcelasTotal}
              onChange={(e) => setAndamento({ ...andamento, parcelasTotal: Number(e.target.value) })}
            />
          </label>
          <p className="col-span-3 text-xs text-muted -mt-1">
            A parcela {andamento.parcelaAtual}/{andamento.parcelasTotal} cai na fatura que vence em{" "}
            <span className="text-gray-200">
              {NOMES_MESES[mes - 1]} {ano}
            </span>{" "}
            (o mês escolhido na tela).{" "}
            {andamento.parcelasTotal > andamento.parcelaAtual
              ? `Depois dela faltam ${andamento.parcelasTotal - andamento.parcelaAtual}.`
              : "É a última."}
          </p>
          <div className="col-span-3">{seletorCategoria}</div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <label>
            <span className="text-xs text-muted">
              {form.recorrente ? "Valor por mês (R$, pode ficar 0)" : "Valor total (R$)"}
            </span>
            <input
              className="input w-full mt-1"
              type="number"
              step="0.01"
              min={form.recorrente ? 0 : 0.01}
              required
              value={form.valor_total}
              onChange={(e) => update("valor_total", Number(e.target.value))}
            />
          </label>
          {!form.recorrente && (
            <label>
              <span className="text-xs text-muted">Parcelas</span>
              <input
                className="input w-full mt-1"
                type="number"
                min={1}
                max={60}
                required
                value={form.parcelas}
                onChange={(e) => update("parcelas", Number(e.target.value))}
              />
            </label>
          )}
          <label>
            <span className="text-xs text-muted">
              {form.recorrente ? "Primeira cobrança" : "Data da compra"}
            </span>
            <input
              className="input w-full mt-1"
              type="date"
              required
              value={form.data_compra}
              onChange={(e) => update("data_compra", e.target.value)}
            />
          </label>
          {seletorCategoria}
        </div>
      )}

      {modo === "nova" && (
        <label className="flex items-center gap-3 rounded-lg bg-white/5 px-3 py-2.5 cursor-pointer">
          <input
            type="checkbox"
            checked={form.recorrente}
            onChange={(e) => marcarFixa(e.target.checked)}
            className="h-4 w-4 accent-accent"
          />
          <div>
            <p className="text-sm font-medium">É uma assinatura (cobra todo mês)</p>
            <p className="text-xs text-muted">
              Streaming de música, de vídeo, internet… Repete em todas as faturas, sem parcelas, e pode ficar
              sem valor.
            </p>
          </div>
        </label>
      )}

      <label className="block">
        <span className="text-xs text-muted">Tags (separadas por vírgula)</span>
        <input
          className="input w-full mt-1"
          value={tagsTexto}
          onChange={(e) => setTagsTexto(e.target.value)}
          placeholder="ex.: assinatura, casa, presente"
        />
      </label>

      {modo === "nova" && !form.recorrente && (
        <div className="text-sm text-muted">
          {form.parcelas > 1 ? (
            <>
              {form.parcelas}× de{" "}
              <span className="text-accent-glow font-semibold">{formatarReal(valorParcela)}</span>
              {sobra > 0 && (
                <>
                  {" "}
                  ({sobra === 1 ? "a última" : `as ${sobra} últimas`} de {formatarReal(valorParcela + 0.01)})
                </>
              )}
            </>
          ) : (
            <>À vista</>
          )}
        </div>
      )}

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
