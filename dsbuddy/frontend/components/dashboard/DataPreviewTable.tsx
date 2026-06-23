"use client";

import { useState } from "react";
import { ChevronDownIcon, ChevronUpIcon } from "lucide-react";
import type { ColumnProfile } from "@/lib/types";

interface Props {
  rows: Record<string, unknown>[];
  columns: ColumnProfile[];
  semanticLabels: Record<string, string> | null;
}

const SEMANTIC_COLORS: Record<string, string> = {
  age: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  monetary_amount: "bg-green-500/10 text-green-600 dark:text-green-400",
  identifier: "bg-gray-500/10 text-gray-500",
  date: "bg-purple-500/10 text-purple-600 dark:text-purple-400",
  category: "bg-orange-500/10 text-orange-600 dark:text-orange-400",
  boolean: "bg-pink-500/10 text-pink-600 dark:text-pink-400",
  free_text: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
  geographic: "bg-teal-500/10 text-teal-600 dark:text-teal-400",
  percentage: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400",
  score: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400",
};

function isNumeric(col: ColumnProfile) {
  return col.mean !== null;
}

function formatCell(val: unknown, numeric: boolean): string {
  if (val === null || val === undefined) return "";
  if (typeof val === "number") {
    return numeric ? val.toLocaleString(undefined, { maximumFractionDigits: 4 }) : String(val);
  }
  return String(val);
}

export function DataPreviewTable({ rows, columns, semanticLabels }: Props) {
  const [open, setOpen] = useState(false);

  if (!rows.length) return null;

  const colNames = columns.map((c) => c.name);

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Data Preview
          </span>
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
            first {rows.length} rows
          </span>
        </div>
        {open ? (
          <ChevronUpIcon className="h-3.5 w-3.5 text-muted-foreground" />
        ) : (
          <ChevronDownIcon className="h-3.5 w-3.5 text-muted-foreground" />
        )}
      </button>

      {open && (
        <div className="border-t border-border overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="sticky left-0 z-10 bg-muted/60 px-3 py-2 text-left font-mono text-[10px] text-muted-foreground">
                  #
                </th>
                {colNames.map((col) => {
                  const cp = columns.find((c) => c.name === col);
                  const label = semanticLabels?.[col];
                  const numeric = cp ? isNumeric(cp) : false;
                  return (
                    <th
                      key={col}
                      className={`px-3 py-2 font-medium text-foreground/80 ${numeric ? "text-right" : "text-left"}`}
                    >
                      <div className="flex flex-col gap-0.5">
                        <span className="font-mono text-[10px] text-foreground">{col}</span>
                        <div className="flex items-center gap-1">
                          <span className="text-[9px] text-muted-foreground">{cp?.dtype ?? ""}</span>
                          {label && label !== "unknown" && (
                            <span className={`rounded px-1 py-0 text-[9px] font-medium ${SEMANTIC_COLORS[label] ?? ""}`}>
                              {label.replace("_", " ")}
                            </span>
                          )}
                        </div>
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, ri) => (
                <tr
                  key={ri}
                  className="border-b border-border/50 hover:bg-muted/20 transition-colors"
                >
                  <td className="sticky left-0 z-10 bg-card px-3 py-1.5 font-mono text-[10px] text-muted-foreground">
                    {ri + 1}
                  </td>
                  {colNames.map((col) => {
                    const cp = columns.find((c) => c.name === col);
                    const numeric = cp ? isNumeric(cp) : false;
                    const val = row[col];
                    const isEmpty = val === null || val === undefined || val === "";
                    return (
                      <td
                        key={col}
                        className={`px-3 py-1.5 ${numeric ? "text-right font-mono" : "text-left"} ${isEmpty ? "text-destructive/50 italic" : "text-foreground/90"} max-w-[180px] truncate`}
                        title={isEmpty ? "missing" : String(val)}
                      >
                        {isEmpty ? "—" : formatCell(val, numeric)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
