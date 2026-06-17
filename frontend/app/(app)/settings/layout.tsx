import type { ReactNode } from "react";
import Link from "next/link";
import { PageHeader, TitleAccent } from "@/components/ui/PageHeader";
import styles from "./layout.module.css";

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <PageHeader
        glyph="&#9881;"
        title={
          <>
            Account <TitleAccent>settings</TitleAccent>
          </>
        }
      />
      <div className={styles.settings}>
        <nav className={styles.settingsNav}>
          <Link href="/settings/profile" className={styles.navLink}>
            Profile
          </Link>
        </nav>
        <div>{children}</div>
      </div>
    </>
  );
}
