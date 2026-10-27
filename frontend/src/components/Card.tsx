import { type ReactNode } from "react";

interface CardProps {
  titulo: string;
  valor: ReactNode;
  cor?: "accent" | "success" | "danger" | "warning" | "muted";
  legenda?: string;
}

const corValor: Record<NonNullable<CardProps["cor"]>, string> = {
  accent: "text-gray-100",
  muted: "text-gray-100",
  success: "text-success",
  danger: "text-danger",
  warning: "text-warning",
};

export default function Card({ titulo, valor, cor = "accent", legenda }: CardProps) {
  return (
    <div className="card">
      <p className="text-sm text-muted">{titulo}</p>
      <div className={["mt-1.5 text-2xl font-semibold tracking-tight truncate", corValor[cor]].join(" ")}>
        {valor}
      </div>
      {legenda && <p className="mt-1 text-xs text-muted">{legenda}</p>}
    </div>
  );
}
