import type { Metadata } from "next";
import type { ReactNode } from "react";
import { fontVariables } from "@/lib/fonts";
import { Shell } from "@/components/shell/Shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Syntrix",
  description: "Communities for gamers, IT admins, and developers.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={fontVariables}>
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
