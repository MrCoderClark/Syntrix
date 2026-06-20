"use client";

import { useEffect, useRef, useCallback } from "react";
import styles from "./RichContent.module.css";

interface RichContentProps {
  html: string;
  className?: string;
}

let mermaidIdCounter = 0;
let mermaidInitialized = false;

export function RichContent({ html, className }: RichContentProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const renderMermaid = useCallback(async () => {
    const container = containerRef.current;
    if (!container) return;

    const codeBlocks = container.querySelectorAll<HTMLElement>(
      "code.language-mermaid",
    );
    if (codeBlocks.length === 0) return;

    const mermaid = (await import("mermaid")).default;
    if (!mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        theme: "base",
        themeVariables: {
          primaryColor: "#e8e1d4",
          primaryTextColor: "#1c1815",
          primaryBorderColor: "#d9d0bd",
          lineColor: "#4a4239",
          secondaryColor: "#f4d4c9",
          tertiaryColor: "#f6f3ec",
          fontFamily: "var(--font-body-family, system-ui, sans-serif)",
          fontSize: "14px",
        },
      });
      mermaidInitialized = true;
    }

    for (const codeEl of codeBlocks) {
      const pre = codeEl.parentElement;
      if (!pre || pre.tagName !== "PRE") continue;

      const source = codeEl.textContent ?? "";
      const id = `mermaid-${++mermaidIdCounter}`;

      try {
        const { svg } = await mermaid.render(id, source);
        const wrapper = document.createElement("div");
        wrapper.className = styles.mermaidSvg;
        wrapper.innerHTML = svg;
        pre.replaceWith(wrapper);
      } catch {
        const errEl = document.createElement("div");
        errEl.className = styles.mermaidError;
        errEl.textContent = "Diagram couldn't be rendered.";
        pre.insertAdjacentElement("beforebegin", errEl);
      }
    }
  }, []);

  useEffect(() => {
    renderMermaid();
  }, [html, renderMermaid]);

  return (
    <div
      ref={containerRef}
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
