import { useState } from "react";
import { NOMES_MESES } from "../lib/constantes";

interface Props {
  mes: number;
  ano: number;
  aoMudar: (mes: number, ano: number) => void;
}

const ANO_MIN = 2000;
const ANO_MAX = 2100;

export default function SeletorMes({ mes, ano, aoMudar }: Props) {
  const [anoTexto, setAnoTexto] = useState(String(ano));
  const [anoRecebido, setAnoRecebido] = useState(ano);
  if (ano !== anoRecebido) {
    setAnoRecebido(ano);
    setAnoTexto(String(ano));
  }

  function mudarAno(texto: string) {
    const limpo = texto.replace(/\D/g, "").slice(0, 4);
    setAnoTexto(limpo);
    const numero = Number(limpo);
    if (limpo.length === 4 && numero >= ANO_MIN && numero <= ANO_MAX && numero !== ano) {
      aoMudar(mes, numero);
    }
  }

  return (
    <>
      <select
        className="input"
        value={mes}
        onChange={(e) => aoMudar(Number(e.target.value), ano)}
        aria-label="Mês"
      >
        {NOMES_MESES.map((nome, i) => (
          <option key={nome} value={i + 1}>
            {nome}
          </option>
        ))}
      </select>
      <input
        className="input w-24"
        inputMode="numeric"
        aria-label="Ano"
        value={anoTexto}
        onChange={(e) => mudarAno(e.target.value)}
        onBlur={() => setAnoTexto(String(ano))}
      />
    </>
  );
}
