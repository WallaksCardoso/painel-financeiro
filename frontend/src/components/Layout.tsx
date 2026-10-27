import { Outlet } from "react-router-dom";
import { sistemaApi } from "../api";
import { OpcoesProvider } from "../contexts/Opcoes";
import { PeriodoProvider } from "../contexts/Periodo";
import Sidebar from "./Sidebar";
import Toaster from "./Toaster";

export default function Layout() {
  return (
    <OpcoesProvider>
      <PeriodoProvider>
        <div className="flex h-screen">
          <Sidebar aoExportar={sistemaApi.exportar} />
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-7xl mx-auto px-8 py-8">
              <Outlet />
            </div>
          </main>
        </div>
        <Toaster />
      </PeriodoProvider>
    </OpcoesProvider>
  );
}
