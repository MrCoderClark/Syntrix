import type { ReactNode } from "react";
import styles from "./PageHeader.module.css";

interface PageHeaderProps {
  glyph: ReactNode;
  glyphStyle?: React.CSSProperties;
  eyebrow?: string;
  title: ReactNode;
  subtitle?: string;
  actions?: ReactNode;
}

export function PageHeader({
  glyph,
  glyphStyle,
  eyebrow,
  title,
  subtitle,
  actions,
}: PageHeaderProps) {
  return (
    <div className={styles.header}>
      <div className={styles.glyph} style={glyphStyle}>
        {glyph}
      </div>
      <div>
        {eyebrow && <div className={styles.eyebrow}>{eyebrow}</div>}
        <h1 className={styles.title}>{title}</h1>
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </div>
  );
}

export function TitleAccent({ children }: { children: ReactNode }) {
  return <em className={styles.titleAccent}>{children}</em>;
}
