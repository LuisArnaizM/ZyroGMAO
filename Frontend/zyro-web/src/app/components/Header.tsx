"use client";
import { Button, Tooltip, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { UserOutlined, SettingOutlined, ApartmentOutlined, TeamOutlined } from "@ant-design/icons";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "../hooks/useAuth";

export function Header() {
  const { user, isAuthenticated } = useAuth();
  // Construimos las opciones del panel de configuración según permisos
  const configItems: MenuProps["items"] = [
    isAuthenticated && user?.role === "Admin"
      ? {
          key: "users",
          icon: <TeamOutlined />,
          label: <Link href="/admin/users">Usuarios</Link>,
        }
      : null,
    isAuthenticated && (user?.role === "Admin" || user?.role === "Supervisor")
      ? {
          key: "departments",
          icon: <ApartmentOutlined />,
          label: <Link href="/admin/departments">Departamentos</Link>,
        }
      : null,
  ].filter(Boolean);
  return (
    <header className="w-full h-full primary-gradient-light border-b border-gray-200 shadow-sm flex items-center">
      <div className="flex h-full w-full items-center justify-between px-4">
        <div className="flex items-center">
          <Link href="/" aria-label="Home" className="flex items-center">
            <Image src="/zyro.webp" alt="Zyro" width={120} height={20} priority />
          </Link>
        </div>
        <div className="flex items-center gap-2">
          {isAuthenticated && configItems.length > 0 && (
            <Dropdown menu={{ items: configItems }} placement="bottomRight" trigger={["click"]}>
              <Tooltip title="Configuración" placement="left">
                <Button type="text" shape="circle"size="middle" className="text-neutral-600" icon={<SettingOutlined />}>
                </Button>
              </Tooltip>  
            </Dropdown>
          )}
          <Link href="/profile" aria-label="Profile">
            <Tooltip title="Profile">
              <Button
                type="text"
                shape="circle"
                icon={<UserOutlined />}
                size="middle"
                className="text-neutral-500 hover:text-neutral-700"
              />
            </Tooltip>
          </Link>
        </div>
      </div>
    </header>
  );
}