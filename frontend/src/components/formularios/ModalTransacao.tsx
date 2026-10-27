import { useEffect, useState } from "react";
import { toast } from "../../toast";
import { dividasApi, transacoesApi } from "../../api";
import { useOpcoes } from "../../contexts/Opcoes";
import { LABEL_RECORRENCIA, LABEL_SITUACAO, LABEL_TIPO, rotuloSituacao } from "../../lib/constantes";
import { hojeISO } from "../../lib/datas";
import { formatarData, formatarReal } from "../../lib/formatar";
import type { Divida, Transacao, TransacaoInput } from "../../types";
import ModalFormulario from "../Modal";

const TIPOS = Object.keys(LABEL_TIPO) as Array<keyof typeof LABEL_TIPO>;
const SITUACOES = Object.keys(LABEL_SITUACAO) as Array<keyof typeof LABEL_SITUACAO>;
const RECORRENCIAS = Object.keys(LABEL_RECORRENCIA) as Array<keyof typeof LABEL_RECORRENCIA>;

interface Props {
  inicial: TransacaoInput;
  editando: Transacao | null;
  aoFechar: () => void;
  aoSalvar: () => void;
}

export default function ModalTransacao({ inicial, editando, aoFechar, aoSalvar }: Props) {
  const { lista } = useOpcoes();
  const [form, setForm] = useState<TransacaoInput>(inicial);
  const [dividas, setDividas] = useState<Divida[]>([]);

  const categorias = lista("categoria");
  const meios = lista("meio_pagamento");
  const categoria = categorias.some((c) => c.chave === form.categoria)
    ? form.categoria
    : (categorias[0]?.chave ?? form.categoria);
  const meio =
    form.meio_pagamento && meios.length && !meios.some((m) => m.chave === form.meio_pagamento)
      ? null
      : form.meio_pagamento;

  useEffect(() => {
    dividasApi
      .listar()
      .then(setDividas)
      .catch(() => {});
  }, []);

  const [situacaoEscolhida, setSituacaoEscolhida] = useState(editando !== null);

  function update<K extends keyof TransacaoInput>(campo: K, valor: TransacaoInput[K]) {
    if (campo === "situacao") setSituacaoEscolhida(true);
    setForm((f) => {
      const novo = { ...f, [campo]: valor };
      if (campo === "data" && !situacaoEscolhida && typeof valor === "string" && valor) {
        novo.situacao = valor > hojeISO() ? "nao_iniciada" : "concluido";
      }
      return novo;
    });
  }

  async function salvar() {
    const valido: TransacaoInput = { ...form, categoria, meio_pagamento: meio };
    let payload = valido.tipo === "quitacao" ? valido : { ...valido, divida_id: null };
    if (payload.recorrencia !== "parcelado") {
      payload = { ...payload, parcela_atual: null, parcelas_total: null };
    }
    const salvo = editando
      ? await transacoesApi.atualizar(editando.id, payload)
      : await transacoesApi.criar(payload);
    toast.sucesso(`"${salvo.lancamento}" salvo em ${formatarData(salvo.data)}.`);
    aoSalvar();
  }

  return (
    <ModalFormulario
      titulo={editando ? "Editar lançamento" : "Novo lançamento"}
      aoFechar={aoFechar}
      aoEnviar={salvar}
      textoSalvar={editando ? "Salvar" : "Criar"}
      largura="lg"
    >
      <div className="grid grid-cols-2 gap-3">
        <label className="col-span-2">
          <span className="text-xs text-muted">Lançamento</span>
          <input
            className="input w-full mt-1"
            required
            value={form.lancamento}
            onChange={(e) => update("lancamento", e.target.value)}
          />
        </label>
        <label>
          <span className="text-xs text-muted">Tipo</span>
          <select
            className="input w-full mt-1"
            value={form.tipo}
            onChange={(e) => update("tipo", e.target.value as TransacaoInput["tipo"])}
          >
            {TIPOS.map((t) => (
              <option key={t} value={t}>
                {LABEL_TIPO[t]}
              </option>
            ))}
          </select>
        </label>
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
        <label>
          <span className="text-xs text-muted">Valor (R$)</span>
          <input
            className="input w-full mt-1"
            type="number"
            step="0.01"
            min={0}
            value={form.valor}
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
          <span className="text-xs text-muted">Meio de pagamento</span>
          <select
            className="input w-full mt-1"
            value={meio ?? ""}
            onChange={(e) => update("meio_pagamento", e.target.value || null)}
          >
            <option value="">—</option>
            {meios.map((m) => (
              <option key={m.chave} value={m.chave}>
                {m.nome}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="text-xs text-muted">Situação</span>
          <select
            className="input w-full mt-1"
            value={form.situacao}
            onChange={(e) => update("situacao", e.target.value as TransacaoInput["situacao"])}
          >
            {SITUACOES.map((s) => (
              <option key={s} value={s}>
                {rotuloSituacao(s, form.tipo)}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="text-xs text-muted">Recorrência</span>
          <select
            className="input w-full mt-1"
            value={form.recorrencia}
            onChange={(e) => update("recorrencia", e.target.value as TransacaoInput["recorrencia"])}
          >
            {RECORRENCIAS.map((r) => (
              <option key={r} value={r}>
                {LABEL_RECORRENCIA[r]}
              </option>
            ))}
          </select>
        </label>
        {form.recorrencia === "parcelado" && (
          <div className="col-span-2 grid grid-cols-2 gap-3 rounded-lg bg-white/5 p-3">
            <label>
              <span className="text-xs text-muted">Parcela atual (opcional)</span>
              <input
                className="input w-full mt-1"
                type="number"
                min={1}
                max={form.parcelas_total ?? 360}
                value={form.parcela_atual ?? ""}
                onChange={(e) => update("parcela_atual", e.target.value ? Number(e.target.value) : null)}
              />
            </label>
            <label>
              <span className="text-xs text-muted">De quantas</span>
              <input
                className="input w-full mt-1"
                type="number"
                min={1}
                max={360}
                value={form.parcelas_total ?? ""}
                onChange={(e) => update("parcelas_total", e.target.value ? Number(e.target.value) : null)}
              />
            </label>
            <p className="col-span-2 text-[11px] text-muted">
              Informando "7 de 8", os próximos meses são previstos até a última parcela.
            </p>
          </div>
        )}
        {form.tipo === "quitacao" && (
          <label className="col-span-2">
            <span className="text-xs text-muted">Abater da dívida (opcional)</span>
            <select
              className="input w-full mt-1"
              value={form.divida_id ?? ""}
              onChange={(e) => update("divida_id", e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">— Nenhuma</option>
              {dividas.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nome} (falta {formatarReal(d.restante)})
                </option>
              ))}
            </select>
            <span className="text-[11px] text-muted mt-1 block">
              Quitações concluídas vinculadas abatem o saldo da dívida automaticamente.
            </span>
          </label>
        )}
        <label className="col-span-2">
          <span className="text-xs text-muted">Observação (opcional)</span>
          <textarea
            className="input w-full mt-1"
            rows={2}
            value={form.observacao ?? ""}
            onChange={(e) => update("observacao", e.target.value || null)}
          />
        </label>
      </div>
    </ModalFormulario>
  );
}
