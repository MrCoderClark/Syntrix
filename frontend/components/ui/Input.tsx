import type { InputHTMLAttributes, ReactNode } from "react";
import styles from "./Input.module.css";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: ReactNode;
}

export function Input({ icon, className, ...props }: InputProps) {
  return (
    <div className={`${styles.wrap}${className ? ` ${className}` : ""}`}>
      {icon && <span className={styles.icon}>{icon}</span>}
      <input className={styles.input} {...props} />
    </div>
  );
}
