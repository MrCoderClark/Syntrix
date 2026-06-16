import type { ButtonHTMLAttributes, ReactNode } from "react";
import styles from "./IconButton.module.css";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  "aria-label": string;
  children: ReactNode;
}

export function IconButton({ className, children, ...props }: IconButtonProps) {
  return (
    <button
      className={`${styles.iconBtn}${className ? ` ${className}` : ""}`}
      {...props}
    >
      {children}
    </button>
  );
}
