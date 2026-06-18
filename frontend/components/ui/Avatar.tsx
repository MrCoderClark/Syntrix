import styles from "./Avatar.module.css";

interface AvatarProps {
  src?: string;
  alt: string;
  fallback: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  bgColor?: string;
  fgColor?: string;
}

export function Avatar({
  src,
  alt,
  fallback,
  size = "md",
  bgColor,
  fgColor,
}: AvatarProps) {
  return (
    <div
      className={`${styles.avatar} ${styles[size]}`}
      style={
        bgColor
          ? { background: bgColor, color: fgColor ?? "var(--paper)" }
          : undefined
      }
      aria-label={alt}
    >
      {src ? <img className={styles.img} src={src} alt={alt} /> : fallback}
    </div>
  );
}
