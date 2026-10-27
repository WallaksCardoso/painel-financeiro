import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";

const Cartoes = lazy(() => import("./pages/Cartoes"));
const Configuracoes = lazy(() => import("./pages/Configuracoes"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Dividas = lazy(() => import("./pages/Dividas"));
const Fluxo = lazy(() => import("./pages/Fluxo"));
const Mes = lazy(() => import("./pages/Mes"));
const Orcamento = lazy(() => import("./pages/Orcamento"));
const Reserva = lazy(() => import("./pages/Reserva"));
const Transacoes = lazy(() => import("./pages/Transacoes"));

const PAGINAS = [
  { caminho: "fluxo", Pagina: Fluxo },
  { caminho: "mes", Pagina: Mes },
  { caminho: "cartoes", Pagina: Cartoes },
  { caminho: "transacoes", Pagina: Transacoes },
  { caminho: "dashboard", Pagina: Dashboard },
  { caminho: "dividas", Pagina: Dividas },
  { caminho: "reserva", Pagina: Reserva },
  { caminho: "orcamento", Pagina: Orcamento },
  { caminho: "configuracoes", Pagina: Configuracoes },
];

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/fluxo" replace />} />
        {PAGINAS.map(({ caminho, Pagina }) => (
          <Route
            key={caminho}
            path={caminho}
            element={
              <Suspense fallback={<p className="text-muted">Carregando…</p>}>
                <Pagina />
              </Suspense>
            }
          />
        ))}
        <Route path="*" element={<Navigate to="/fluxo" replace />} />
      </Route>
    </Routes>
  );
}
