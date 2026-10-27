import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";

interface Props {
  titulo: string;
  aoFechar: () => void;
  aoEnviar: () => Promise<void>;
  textoSalvar?: string;
  largura?: "md" | "lg";
  children: ReactNode;
}

const LARGURAS = { md: "max-w-lg", lg: "max-w-2xl" };

export default function ModalFormulario({
  titulo,
  aoFechar,
  aoEnviar,
  textoSalvar = "Salvar",
  largura = "md",
  children,
}: Props) {
  const [salvando, setSalvando] = useState(false);
  const comecouNoFundo = useRef(false);

  useEffect(() => {
    const aoTeclar = (e: KeyboardEvent) => e.key === "Escape" && aoFechar();
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [aoFechar]);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (salvando) return;
    setSalvando(true);
    await aoEnviar().catch(() => undefined);
    setSalvando(false);
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4"
      onMouseDown={(e) => {
        comecouNoFundo.current = e.target === e.currentTarget;
      }}
      onClick={(e) => {
        if (comecouNoFundo.current && e.target === e.currentTarget) aoFechar();
      }}
    >
      <form
        onSubmit={enviar}
        className={["card w-full max-h-[90vh] overflow-y-auto space-y-4", LARGURAS[largura]].join(" ")}
      >
        <h2 className="text-xl font-semibold">{titulo}</h2>
        {children}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-ghost" onClick={aoFechar}>
            Cancelar
          </button>
          <button type="submit" className="btn-primary disabled:opacity-60" disabled={salvando}>
            {salvando ? "Salvando…" : textoSalvar}
          </button>
        </div>
      </form>
    </div>
  );
}
