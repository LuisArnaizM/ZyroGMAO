"use client";
import React from "react";
import { LoadingOutlined } from "@ant-design/icons";

type Variant = "primary" | "secondary" | "danger" | "ghost" | "link";
type Size = "sm" | "md" | "lg";

export type AppButtonProps = {
  children?: React.ReactNode;
  variant?: Variant;
  size?: Size;
  block?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  loading?: boolean;
  disabled?: boolean;
  title?: string;
  type?: "button" | "submit" | "reset";
  className?: string;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
};

const cx = (...c: Array<string | false | undefined>) => c.filter(Boolean).join(" ");

export function AppButton({
  children,
  variant = "primary",
  size = "md",
  block = false,
  icon,
  iconRight,
  loading = false,
  disabled = false,
  title,
  type = "button",
  className,
  onClick,
}: AppButtonProps) {
  const base =
  "btn";

  const byVariant: Record<Variant, string> = {
    primary: "btn--primary",
    secondary: "btn--secondary",
    danger: "btn--danger",
    ghost: "btn--ghost",
    link: "btn--link",
  };

  const bySize: Record<Size, string> = {
    sm: "btn--sm",
    md: "btn--md",
    lg: "btn--lg",
  };

  const cls = cx(base, byVariant[variant], bySize[size], block && "btn--block", className);

  return (
    <button type={type} className={cls} onClick={onClick} disabled={disabled || loading} title={title}>
      {loading ? (
        <LoadingOutlined className="animate-spin" />
      ) : (
        icon && <span className="text-[1.05em] leading-none">{icon}</span>
      )}
      {children && <span>{children}</span>}
      {!loading && iconRight && <span className="text-[1.05em] leading-none">{iconRight}</span>}
    </button>
  );
}

export default AppButton;
