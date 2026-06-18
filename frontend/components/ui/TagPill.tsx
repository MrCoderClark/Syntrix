import Link from "next/link";
import styles from "./TagPill.module.css";

interface TagPillProps {
  name: string;
  color?: string | null;
  href?: string;
  onRemove?: () => void;
}

export function TagPill({ name, color, href, onRemove }: TagPillProps) {
  const inner = (
    <>
      {color && <span className={styles.dot} style={{ background: color }} />}
      <span className={styles.name}>{name}</span>
      {onRemove && (
        <button
          type="button"
          className={styles.removeBtn}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onRemove();
          }}
          aria-label={`Remove ${name}`}
        >
          &times;
        </button>
      )}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={styles.pill}>
        {inner}
      </Link>
    );
  }

  return <span className={styles.pill}>{inner}</span>;
}
