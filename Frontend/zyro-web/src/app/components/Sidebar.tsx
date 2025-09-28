"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../hooks/useAuth";
import { InboxOutlined, DollarOutlined, FireOutlined, HomeOutlined, PieChartOutlined, ToolOutlined, AuditOutlined } from "@ant-design/icons";

const navItems = [
  { href: "/", label: "Home", icon: <HomeOutlined size={28} /> },
  { href: "/dashboard", label: "Dashboard", icon: <PieChartOutlined size={28} /> },
  { href: "/asset", label: "Assets", icon: <DollarOutlined size={28} /> },
  { href: "/inventory", label: "Inventory", icon: <InboxOutlined size={28} /> },
  { href: "/workorders", label: "Work Orders", icon: <ToolOutlined size={28} /> },
  { href: "/failures", label: "Failures", icon: <FireOutlined size={28} /> },
  { href: "/planner", label: "Planner", icon: <AuditOutlined size={26} /> },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, loading } = useAuth();

  // Filtrar items protegidos cuando no hay autenticación
  const protectedRoutes = new Set(["/asset", "/inventory", "/workorders", "/failures", "/planner"]);
  const visibleItems = navItems.filter((item) => {
    if (loading) return !protectedRoutes.has(item.href);
    if (!isAuthenticated && protectedRoutes.has(item.href)) return false;
    return true;
  });
  const activeCls = (href: string) => {
    if (href === '/') {
      return pathname === '/' ? 'lborder primary-gradient-dark translate-x-0.5 scale-105' : 'lborder-light link-hover';
    }
    const isExact = pathname === href;
    const isNested = pathname.startsWith(href + '/');
    return (isExact || isNested)
      ? 'lborder primary-gradient-dark translate-x-0.5 scale-105'
      : 'lborder-light link-hover';
  };

  return (
    <aside
      className={"sticky top-0 h-screen px-2 py-4 backdrop-blur w-45"}
      aria-label="Sidebar"
    >
    <nav className="flex flex-col gap-2">
        {visibleItems.map((item) => {
          const content = (
            <Link
              key={item.href}
              href={item.href}
              className={`group border-light flex items-center gap-2 rounded-xl px-3 py-2 min-w-0 transition-all duration-300 ease-in-out transform ${activeCls(
                item.href
              )}`}
            >
              <span className="text-2xl">{item.icon}</span>
              <span className="text-sm font-bold truncate">{item.label}</span>
            </Link>
          );
      return content;
        })}
      </nav>
    </aside>
  );
}