"use client";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { AntdProvider } from "./providers/AntdProvider";

import "./styles/globals.css";
import { ReduxProvider } from "./providers/ReduxProvider";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html suppressHydrationWarning>
      <body className="h-screen w-screen overflow-hidden">
        <ReduxProvider>
          <AntdProvider>
            {/* Contenedor raíz sin scroll global */}
            <div className="h-screen w-screen">
              {/* Header fijo */}
              <div className="fixed top-0 left-0 right-0 h-16 z-50 flex items-stretch bg-white/95 backdrop-blur border-b border-gray-200 shadow-sm">
                {/* Header ocupa todo el ancho; el propio componente puede tener padding interno */}
                <Header />
              </div>
              {/* Sidebar fijo bajo el header */}
              <div className="fixed top-16 left-0 bottom-0 w-48 z-40 border-r border-gray-200 bg-white pt-2">
                {/* Separación superior para que el contenido no quede pegado al header */}
                <Sidebar />
              </div>
              {/* Área de contenido con scroll interno */}
              <main className="absolute top-16 left-48 right-0 bottom-0 overflow-auto bg-gray-50">
                <div className="p-4 min-h-full">{children}</div>
              </main>
            </div>
          </AntdProvider>
        </ReduxProvider>
      </body>
    </html>
  );
}