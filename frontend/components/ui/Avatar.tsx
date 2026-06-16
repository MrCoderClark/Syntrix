import Image from "next/image";
import styles from "./Avatar.module.css";

interface AvatarProps {
  src?: string;
  alt: string;
  fallback: string;
  size?: "sm" | "md" | "lg";
  bgColor?: string;
  fgColor?: string;
}

const SIZE_PX = { sm: 26, md: 40, lg: 56 } as const;

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
      {src ? (
        <Image
          src={src}
          alt={alt}
          width={SIZE_PX[size]}
          height={SIZE_PX[size]}
        />
      ) : (
        fallback
      )}
    </div>
  );
}
