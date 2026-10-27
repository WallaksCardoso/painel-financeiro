export function hojeISO(): string {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

export function mesAtual(): { mes: number; ano: number } {
  const d = new Date();
  return { mes: d.getMonth() + 1, ano: d.getFullYear() };
}

export function dataPadrao(mes: number, ano: number): string {
  const atual = mesAtual();
  if (atual.mes === mes && atual.ano === ano) return hojeISO();
  return `${ano}-${String(mes).padStart(2, "0")}-01`;
}
