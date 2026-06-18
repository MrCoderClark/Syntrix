"use client";

import { useState, type ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import styles from "./Shell.module.css";

export function Shell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className={styles.app}>
      {menuOpen && (
        <div className={styles.overlay} onClick={() => setMenuOpen(false)} />
      )}
      <Sidebar mobileOpen={menuOpen} onClose={() => setMenuOpen(false)} />
      <main className={styles.main}>
        <Topbar onMenuToggle={() => setMenuOpen((o) => !o)} />
        {children}
      </main>
    </div>
  );
}
