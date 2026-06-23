"use client";

import { useState, useRef, useEffect, type ReactNode } from "react";
import { useAssist, TERM_DEFINITIONS } from "@/lib/assist-context";

interface TermProps {
  name: string;
  children: ReactNode;
}

export function Term({ name, children }: TermProps) {
  const { on } = useAssist();
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const def = TERM_DEFINITIONS[name.toLowerCase()];

  useEffect(() => {
    if (!visible) return;
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setVisible(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [visible]);

  if (!on || !def) return <>{children}</>;

  return (
    <span
      ref={ref}
      className="relative inline cursor-help border-b border-dashed border-muted-foreground/50"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <span className="absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2 rounded-md border border-border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-lg">
          <span className="mb-1 block font-semibold capitalize">{name}</span>
          {def}
          <span className="absolute -bottom-1.5 left-1/2 h-2.5 w-2.5 -translate-x-1/2 rotate-45 border-b border-r border-border bg-popover" />
        </span>
      )}
    </span>
  );
}
