import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { removerToast, useToasts, type TipoToast } from "../toast";

const ESTILO: Record<TipoToast, { classe: string; Icon: typeof Info }> = {
  erro: { classe: "border-danger/40 text-gray-100 [&>svg]:text-danger", Icon: AlertCircle },
  sucesso: { classe: "border-success/40 text-gray-100 [&>svg]:text-success", Icon: CheckCircle2 },
  info: { classe: "border-white/15 text-gray-200", Icon: Info },
};

export default function Toaster() {
  const toasts = useToasts();
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-100 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => {
        const { classe, Icon } = ESTILO[t.tipo];
        return (
          <div
            key={t.id}
            className={["flex items-start gap-3 rounded-md border bg-bg-card px-4 py-3 text-sm", classe].join(
              " ",
            )}
            role="alert"
          >
            <Icon className="h-4 w-4 mt-0.5 shrink-0" />
            <p className="flex-1">{t.mensagem}</p>
            <button
              onClick={() => removerToast(t.id)}
              className="shrink-0 opacity-60 hover:opacity-100"
              aria-label="Fechar"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
