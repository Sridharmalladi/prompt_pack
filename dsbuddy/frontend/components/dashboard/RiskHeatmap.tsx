"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { AgenticInsights, RiskSeverity } from "@/lib/types";

// ── Severity → cell colour ─────────────────────────────────────────────────────

const CELL_STYLES: Record<RiskSeverity, string> = {
  high: "bg-orange-400 text-white dark:bg-orange-500",
  medium: "bg-yellow-300 text-yellow-900 dark:bg-yellow-500 dark:text-white",
  low: "bg-green-200 text-green-900 dark:bg-green-700 dark:text-white",
};

const SEVERITY_ORDER: RiskSeverity[] = ["high", "medium", "low"];

function dominantSeverity(severities: RiskSeverity[]): RiskSeverity {
  for (const s of SEVERITY_ORDER) {
    if (severities.includes(s)) return s;
  }
  return "low";
}

// ── Build heatmap matrix ───────────────────────────────────────────────────────

interface HeatCell {
  severity: RiskSeverity;
  descriptions: string[];
}

interface HeatmapMatrix {
  features: string[];
  riskTypes: string[];
  cells: Record<string, Record<string, HeatCell>>;
}

function buildMatrix(insights: AgenticInsights): HeatmapMatrix {
  // feature → riskType → { severities, descriptions }
  const raw: Record<string, Record<string, { severities: RiskSeverity[]; descs: string[] }>> = {};

  function add(col: string, riskType: string, severity: RiskSeverity, desc: string) {
    if (!col) return;
    raw[col] ??= {};
    raw[col][riskType] ??= { severities: [], descs: [] };
    raw[col][riskType].severities.push(severity);
    raw[col][riskType].descs.push(desc);
  }

  for (const item of (insights.insights ?? [])) {
    const label = item.type.replace(/_/g, " ");
    if ((item.columns ?? []).length > 0) {
      for (const col of item.columns) add(col, label, item.severity, item.message);
    }
  }
  for (const col of (insights.leakage_risk_columns ?? [])) {
    add(col, "leakage risk", "high", "Potential target leakage detected");
  }

  const features = Object.keys(raw);
  const riskTypeSet = new Set<string>();
  for (const ft of Object.values(raw)) Object.keys(ft).forEach((r) => riskTypeSet.add(r));
  const riskTypes = Array.from(riskTypeSet);

  const cells: Record<string, Record<string, HeatCell>> = {};
  for (const feat of features) {
    cells[feat] = {};
    for (const rt of riskTypes) {
      const entry = raw[feat]?.[rt];
      if (entry) {
        cells[feat][rt] = {
          severity: dominantSeverity(entry.severities),
          descriptions: entry.descs,
        };
      }
    }
  }

  return { features, riskTypes, cells };
}

// ── Hover tooltip ─────────────────────────────────────────────────────────────

interface TooltipState {
  feature: string;
  riskType: string;
  cell: HeatCell;
  x: number;
  y: number;
}

// ── Main component ─────────────────────────────────────────────────────────────

interface RiskHeatmapProps {
  insights: AgenticInsights;
}

export function RiskHeatmap({ insights }: RiskHeatmapProps) {
  const selectedFeature = useAppStore((s) => s.selectedFeature);
  const setSelectedFeature = useAppStore((s) => s.setSelectedFeature);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const matrix = buildMatrix(insights);
  const { features, riskTypes, cells } = matrix;

  if (features.length === 0) return null;

  const CELL_W = 36;
  const LABEL_W = 120;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Risk heatmap</h3>
        <p className="text-[10px] text-muted-foreground">
          Hover cells for detail · click row to highlight feature
        </p>
      </div>

      <div className="relative overflow-x-auto rounded-lg border border-border">
        {/* Header row */}
        <div className="flex border-b border-border bg-muted/30">
          <div style={{ width: LABEL_W, minWidth: LABEL_W }} className="shrink-0 px-2 py-1" />
          {riskTypes.map((rt) => (
            <div
              key={rt}
              style={{ width: CELL_W, minWidth: CELL_W }}
              className="shrink-0 flex items-end justify-center pb-1"
            >
              <span
                className="text-[8px] text-muted-foreground leading-tight"
                style={{
                  writingMode: "vertical-rl",
                  transform: "rotate(180deg)",
                  maxHeight: 72,
                  overflow: "hidden",
                }}
                title={rt}
              >
                {rt}
              </span>
            </div>
          ))}
        </div>

        {/* Data rows */}
        {features.map((feat) => (
          <div
            key={feat}
            className={cn(
              "flex items-center border-b border-border last:border-b-0 cursor-pointer transition-colors",
              selectedFeature === feat ? "bg-primary/5" : "hover:bg-muted/20"
            )}
            onClick={() =>
              setSelectedFeature(selectedFeature === feat ? null : feat)
            }
          >
            {/* Feature label */}
            <div
              style={{ width: LABEL_W, minWidth: LABEL_W }}
              className="shrink-0 px-2 py-1"
            >
              <span
                className={cn(
                  "text-[10px] font-medium truncate block",
                  selectedFeature === feat && "text-primary"
                )}
                title={feat}
              >
                {feat}
              </span>
            </div>

            {/* Cells */}
            {riskTypes.map((rt) => {
              const cell = cells[feat]?.[rt];
              return (
                <div
                  key={rt}
                  style={{ width: CELL_W, minWidth: CELL_W, height: 28 }}
                  className={cn(
                    "shrink-0 m-0.5 rounded-sm flex items-center justify-center text-[8px] font-bold transition-opacity",
                    cell ? CELL_STYLES[cell.severity] : "bg-muted/30"
                  )}
                  title={cell ? `${feat} · ${rt}: ${cell.severity}` : undefined}
                  onMouseEnter={(e) => {
                    if (cell) {
                      const rect = (e.target as HTMLElement).getBoundingClientRect();
                      setTooltip({ feature: feat, riskType: rt, cell, x: rect.left, y: rect.bottom });
                    }
                  }}
                  onMouseLeave={() => setTooltip(null)}
                >
                  {cell ? cell.severity[0].toUpperCase() : ""}
                </div>
              );
            })}
          </div>
        ))}

        {/* Severity legend */}
        <div className="flex items-center gap-3 px-3 py-2 bg-muted/20 border-t border-border">
          {SEVERITY_ORDER.map((s) => (
            <span key={s} className="flex items-center gap-1">
              <span className={cn("inline-block h-3 w-3 rounded-sm", CELL_STYLES[s])} />
              <span className="text-[9px] text-muted-foreground capitalize">{s}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Floating tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 rounded-lg border border-border bg-popover text-popover-foreground shadow-lg p-3 text-xs max-w-xs pointer-events-none"
          style={{ top: tooltip.y + 8, left: tooltip.x }}
        >
          <p className="font-semibold mb-1">
            {tooltip.feature} — {tooltip.riskType}
          </p>
          <p className="capitalize text-[10px] mb-1.5 font-medium">
            Severity: {tooltip.cell.severity}
          </p>
          {tooltip.cell.descriptions.map((d, i) => (
            <p key={i} className="text-[10px] text-muted-foreground leading-snug">
              {d}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
