import type { ReactNode } from "react";
import styles from "./Tab.module.css";

interface TabStripProps {
  children: ReactNode;
  className?: string;
}

export function TabStrip({ children, className }: TabStripProps) {
  return (
    <div className={`${styles.tabStrip}${className ? ` ${className}` : ""}`}>
      {children}
    </div>
  );
}

interface TabProps {
  active?: boolean;
  onClick?: () => void;
  children: ReactNode;
  count?: string;
}

export function Tab({ active, onClick, children, count }: TabProps) {
  return (
    <button
      className={`${styles.tab}${active ? ` ${styles.active}` : ""}`}
      onClick={onClick}
    >
      {children}
      {count && <span className={styles.count}>({count})</span>}
    </button>
  );
}
