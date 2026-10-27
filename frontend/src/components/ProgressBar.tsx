interface ProgressBarProps {
  valor: number;
  cor?: "accent" | "success" | "danger" | "warning";
  altura?: "sm" | "md" | "lg";
}

const corMap = {
  accent: "bg-accent",
  success: "bg-success",
  danger: "bg-danger",
  warning: "bg-warning",
};

const alturaMap = {
  sm: "h-1",
  md: "h-1.5",
  lg: "h-2",
};

export default function ProgressBar({ valor, cor = "accent", altura = "md" }: ProgressBarProps) {
  const limitado = Math.min(Math.max(valor, 0), 100);
  return (
    <div className={["w-full rounded-full bg-white/[0.06] overflow-hidden", alturaMap[altura]].join(" ")}>
      <div
        className={["h-full rounded-full transition-all duration-500", corMap[cor]].join(" ")}
        style={{ width: `${limitado}%` }}
      />
    </div>
  );
}
