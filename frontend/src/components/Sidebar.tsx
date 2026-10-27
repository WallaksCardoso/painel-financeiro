import {
  CalendarDays,
  ChevronDown,
  ChevronRight,
  CreditCard,
  Download,
  LayoutDashboard,
  PiggyBank,
  Receipt,
  Settings,
  Target,
  TrendingUp,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

interface ItemMenu {
  to: string;
  label: string;
  Icon: LucideIcon;
}

const principais: ItemMenu[] = [
  { to: "/fluxo", label: "Fluxo de caixa", Icon: TrendingUp },
  { to: "/mes", label: "Mês", Icon: CalendarDays },
  { to: "/cartoes", label: "Cartões", Icon: CreditCard },
  { to: "/transacoes", label: "Transações", Icon: Receipt },
  { to: "/dashboard", label: "Dashboard", Icon: LayoutDashboard },
];

const mais: ItemMenu[] = [
  { to: "/dividas", label: "Dívidas", Icon: Target },
  { to: "/reserva", label: "Reserva", Icon: PiggyBank },
  { to: "/orcamento", label: "Orçamento", Icon: Wallet },
  { to: "/configuracoes", label: "Configurações", Icon: Settings },
];

function LinkMenu({ to, label, Icon }: ItemMenu) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors",
          isActive
            ? "bg-white/[0.07] text-gray-100"
            : "text-gray-400 hover:bg-white/[0.04] hover:text-gray-100",
        ].join(" ")
      }
    >
      <Icon className="h-4 w-4 opacity-70" />
      {label}
    </NavLink>
  );
}

interface Props {
  aoExportar: () => void;
}

export default function Sidebar({ aoExportar }: Props) {
  const { pathname } = useLocation();
  const [maisAberto, setMaisAberto] = useState(() => mais.some((i) => pathname.startsWith(i.to)));

  return (
    <aside className="w-56 shrink-0 border-r border-white/[0.07] flex flex-col">
      <div className="px-5 h-14 flex items-center">
        <span className="text-sm font-semibold tracking-tight">Painel financeiro</span>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-0.5">
        {principais.map((item) => (
          <LinkMenu key={item.to} {...item} />
        ))}
        <button
          type="button"
          onClick={() => setMaisAberto((v) => !v)}
          className="w-full flex items-center gap-2 px-2.5 pt-5 pb-1.5 text-xs text-muted hover:text-gray-300 transition-colors"
        >
          {maisAberto ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          Mais
        </button>
        {maisAberto && mais.map((item) => <LinkMenu key={item.to} {...item} />)}
      </nav>

      <div className="px-3 py-3 border-t border-white/[0.07]">
        <button
          onClick={aoExportar}
          className="w-full flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm text-gray-400 hover:bg-white/[0.04] hover:text-gray-100 transition-colors"
          title="Baixar um backup dos seus dados em JSON"
        >
          <Download className="h-4 w-4" />
          Exportar dados
        </button>
      </div>
    </aside>
  );
}
