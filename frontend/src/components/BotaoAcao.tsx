import { useState, type ReactNode } from "react";

interface Props {
  acao: () => Promise<unknown>;
  className?: string;
  title?: string;
  children: ReactNode;
}

export default function BotaoAcao({ acao, className = "btn-ghost", title, children }: Props) {
  const [ocupado, setOcupado] = useState(false);
  return (
    <button
      type="button"
      className={[className, "disabled:opacity-60 disabled:cursor-wait"].join(" ")}
      title={title}
      disabled={ocupado}
      onClick={async () => {
        if (ocupado) return;
        setOcupado(true);
        await acao().catch(() => undefined);
        setOcupado(false);
      }}
    >
      {children}
    </button>
  );
}
