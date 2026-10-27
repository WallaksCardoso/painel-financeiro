import axios from "axios";
import type {
  Cartao,
  CartaoInput,
  CategoriaTotal,
  CompraCartao,
  CompraCartaoInput,
  CompraEmAndamentoInput,
  DashboardCompleto,
  Divida,
  DividaInput,
  FaturaMes,
  FaturaPaga,
  FaturaPagaInput,
  GrupoOpcao,
  Opcao,
  PlanoMes,
  PlanoMesInput,
  ResumoMesPlano,
  MovimentoReserva,
  MovimentoReservaInput,
  OrcamentoCategoria,
  OrcamentoInput,
  Projecao,
  ProximaConta,
  ReservaSaldo,
  ResumoMes,
  Transacao,
  TransacaoInput,
} from "./types";

import { mensagemDeErro } from "./lib/erros";
import { toast } from "./toast";

const http = axios.create({ baseURL: "/api" });

http.interceptors.response.use(
  (r) => r,
  (erro) => {
    toast.erro(
      erro.response
        ? mensagemDeErro(erro.response.data?.detail, erro.response.status)
        : "Sem conexão com o backend. Ele está rodando?",
    );
    return Promise.reject(erro);
  },
);

export const transacoesApi = {
  listar: (filtros?: { mes?: number; ano?: number; tipo?: string; categoria?: string; situacao?: string }) =>
    http.get<Transacao[]>("/transacoes", { params: filtros }).then((r) => r.data),
  obter: (id: number) => http.get<Transacao>(`/transacoes/${id}`).then((r) => r.data),
  criar: (data: TransacaoInput) => http.post<Transacao>("/transacoes", data).then((r) => r.data),
  atualizar: (id: number, data: Partial<TransacaoInput>) =>
    http.patch<Transacao>(`/transacoes/${id}`, data).then((r) => r.data),
  remover: (id: number) => http.delete(`/transacoes/${id}`).then(() => undefined),
  gerarRecorrentes: (mes: number, ano: number) =>
    http
      .post<Transacao[]>("/transacoes/gerar-recorrentes", null, { params: { mes, ano } })
      .then((r) => r.data),
  encerrarRecorrencia: (lancamento: string, categoria: string, mes: number, ano: number) =>
    http
      .post<{ removidos: number }>("/transacoes/encerrar-recorrencia", { lancamento, categoria, mes, ano })
      .then((r) => r.data),
};

export const dividasApi = {
  listar: () => http.get<Divida[]>("/dividas").then((r) => r.data),
  criar: (data: DividaInput) => http.post<Divida>("/dividas", data).then((r) => r.data),
  atualizar: (id: number, data: Partial<DividaInput>) =>
    http.patch<Divida>(`/dividas/${id}`, data).then((r) => r.data),
  remover: (id: number) => http.delete(`/dividas/${id}`).then(() => undefined),
};

export const reservaApi = {
  listar: () => http.get<MovimentoReserva[]>("/reserva").then((r) => r.data),
  saldo: () => http.get<ReservaSaldo>("/reserva/saldo").then((r) => r.data),
  criar: (data: MovimentoReservaInput) => http.post<MovimentoReserva>("/reserva", data).then((r) => r.data),
  atualizar: (id: number, data: Partial<MovimentoReservaInput>) =>
    http.patch<MovimentoReserva>(`/reserva/${id}`, data).then((r) => r.data),
  remover: (id: number) => http.delete(`/reserva/${id}`).then(() => undefined),
};

export const orcamentoApi = {
  listar: (mes?: number, ano?: number) =>
    http.get<OrcamentoCategoria[]>("/orcamento", { params: { mes, ano } }).then((r) => r.data),
  criar: (data: OrcamentoInput) => http.post<OrcamentoCategoria>("/orcamento", data).then((r) => r.data),
  atualizar: (id: number, data: Partial<OrcamentoInput>) =>
    http.patch<OrcamentoCategoria>(`/orcamento/${id}`, data).then((r) => r.data),
  remover: (id: number) => http.delete(`/orcamento/${id}`).then(() => undefined),
};

export const cartoesApi = {
  listar: () => http.get<Cartao[]>("/cartoes").then((r) => r.data),
  criar: (data: CartaoInput) => http.post<Cartao>("/cartoes", data).then((r) => r.data),
  atualizar: (id: number, data: Partial<CartaoInput>) =>
    http.patch<Cartao>(`/cartoes/${id}`, data).then((r) => r.data),
  remover: (id: number) => http.delete(`/cartoes/${id}`).then(() => undefined),

  listarCompras: (cartao_id?: number) =>
    http.get<CompraCartao[]>("/cartoes/compras", { params: { cartao_id } }).then((r) => r.data),
  criarCompra: (data: CompraCartaoInput) =>
    http.post<CompraCartao>("/cartoes/compras", data).then((r) => r.data),
  criarCompraEmAndamento: (data: CompraEmAndamentoInput) =>
    http.post<CompraCartao>("/cartoes/compras/em-andamento", data).then((r) => r.data),
  atualizarCompraEmAndamento: (id: number, data: CompraEmAndamentoInput) =>
    http.put<CompraCartao>(`/cartoes/compras/${id}/em-andamento`, data).then((r) => r.data),
  atualizarCompra: (id: number, data: Partial<CompraCartaoInput>) =>
    http.patch<CompraCartao>(`/cartoes/compras/${id}`, data).then((r) => r.data),
  removerCompra: (id: number) => http.delete(`/cartoes/compras/${id}`).then(() => undefined),

  faturaQueVence: (cartao_id: number, mes: number, ano: number) =>
    http
      .get<FaturaMes>(`/cartoes/${cartao_id}/fatura`, { params: { mes, ano, vence_em: true } })
      .then((r) => r.data),

  marcarFaturaPaga: (cartao_id: number, data: FaturaPagaInput) =>
    http.post<FaturaPaga>(`/cartoes/${cartao_id}/faturas`, data).then((r) => r.data),
  desmarcarFaturaPaga: (fatura_paga_id: number) =>
    http.delete(`/cartoes/faturas/${fatura_paga_id}`).then(() => undefined),
};

export const sistemaApi = {
  exportar: () => window.open("/api/exportar", "_blank"),
  backup: () => window.open("/api/backup", "_blank"),
};

export const dashboardApi = {
  resumo: (mes?: number, ano?: number) =>
    http.get<ResumoMes>("/dashboard/resumo", { params: { mes, ano } }).then((r) => r.data),
  porCategoria: (mes?: number, ano?: number, tipo: string = "despesa") =>
    http
      .get<CategoriaTotal[]>("/dashboard/por-categoria", { params: { mes, ano, tipo } })
      .then((r) => r.data),
  proximas: (dias?: number) =>
    http.get<ProximaConta[]>("/dashboard/proximas", { params: { dias } }).then((r) => r.data),
  completo: (mes?: number, ano?: number) =>
    http.get<DashboardCompleto>("/dashboard/completo", { params: { mes, ano } }).then((r) => r.data),
};

export const projecaoApi = {
  obter: (meses: number, mes?: number, ano?: number) =>
    http.get<Projecao>("/projecao", { params: { meses, mes, ano } }).then((r) => r.data),
};

export const mesApi = {
  resumo: (mes: number, ano: number) => http.get<ResumoMesPlano>(`/mes/${ano}/${mes}`).then((r) => r.data),
  salvarPlano: (mes: number, ano: number, data: PlanoMesInput) =>
    http.put<PlanoMes>(`/mes/${ano}/${mes}/plano`, data).then((r) => r.data),
};

export const opcoesApi = {
  listar: () => http.get<Opcao[]>("/opcoes").then((r) => r.data),
  criar: (grupo: GrupoOpcao, nome: string) =>
    http.post<Opcao>("/opcoes", { grupo, nome }).then((r) => r.data),
  atualizar: (id: number, data: { nome?: string; ordem?: number }) =>
    http.patch<Opcao>(`/opcoes/${id}`, data).then((r) => r.data),
  remover: (id: number) => http.delete(`/opcoes/${id}`).then(() => undefined),
};

export const configApi = {
  ler: (chave: string) =>
    http.get<{ chave: string; valor: string | null }>(`/config/${chave}`).then((r) => r.data.valor),
  salvar: (chave: string, valor: string) => http.put(`/config/${chave}`, { valor }).then(() => undefined),
};
