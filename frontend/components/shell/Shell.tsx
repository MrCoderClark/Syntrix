import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import styles from "./Shell.module.css";

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className={styles.app}>
      <Sidebar />
      <main className={styles.main}>
        <Topbar />
        {children}
      </main>
    </div>
  );
}
