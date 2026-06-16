import type { ButtonHTMLAttributes, ReactNode } from "react";
import styles from "./Button.module.css";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "ghost";
  children: ReactNode;
}

export function Button({
  variant = "default",
  className,
  children,
  ...props
}: ButtonProps) {
  const cls = [
    styles.btn,
    variant !== "default" ? styles[variant] : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={cls} {...props}>
      {children}
    </button>
  );
}
