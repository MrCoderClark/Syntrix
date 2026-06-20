import type { Metadata } from "next";
import type { ReactNode } from "react";
import { fontVariables } from "@/lib/fonts";
import "./globals.css";
import "./pygments-theme.css";
import "./katex-fonts.css";

export const metadata: Metadata = {
  title: "Syntrix",
  description: "Communities for gamers, IT admins, and developers.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={fontVariables}>
      <body>{children}</body>
    </html>
  );
}
