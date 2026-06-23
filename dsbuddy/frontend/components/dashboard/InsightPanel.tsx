"use client";

import { useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Term } from "@/components/Term";
import type { AgenticInsights, Insight, ModelFitResult, Recommendation } from "@/lib/types";
import { cn } from "@/lib/utils";

const SEVERITY_DOT: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-green-500",
};

function SeverityDot({ severity }: { severity: string }) {
  return (
    <span className={cn("inline-block h-1.5 w-1.5 rounded-full shrink-0 mt-1.5", SEVERITY_DOT[severity] ?? "bg-muted-foreground")} />
  );
}

// ── Model scores panel ────────────────────────────────────────────────────────

const PRIMARY_KEYS = ["accuracy", "r2", "auc"];

function ModelScoresPanel({ scores }: { scores: ModelFitResult[] }) {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="space-y-2">
      {scores.map((m) => {
        const isSelected = selected === m.model_name;
        const primaryKey = PRIMARY_KEYS.find((k) => k in m.metrics);
        const primaryVal = primaryKey != null ? m.metrics[primaryKey] : null;

        return (
          <button
            key={m.model_name}
            onClick={() => setSelected(isSelected ? null : m.model_name)}
            className={cn(
              "w-full text-left rounded border px-3 py-2.5 transition-all",
              isSelected ? "border-foreground/30 bg-secondary" : "border-border/50 hover:border-foreground/20 hover:bg-secondary/60",
              m.error && "opacity-50"
            )}
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs font-medium text-foreground">{m.model_name}</span>
              <div className="flex items-center gap-3 shrink-0">
                {m.error ? (
                  <span className="text-[10px] text-muted-foreground">{m.error}</span>
                ) : primaryVal != null ? (
                  <span className="font-mono text-xs font-semibold text-foreground">
                    {(primaryVal * 100).toFixed(1)}%
                  </span>
                ) : null}
                <span className="text-[10px] text-muted-foreground">{m.fit_time_seconds}s</span>
              </div>
            </div>

            {!m.error && primaryVal != null && (
              <div className="mt-2 h-px w-full bg-border overflow-visible">
                <div
                  className="h-px bg-foreground/60 transition-all duration-700"
                  style={{ width: `${Math.max(0, Math.min(100, primaryVal * 100))}%` }}
                />
              </div>
            )}

            {isSelected && !m.error && Object.keys(m.metrics).length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-4 border-t border-border/40 pt-2.5">
                {Object.entries(m.metrics).map(([k, v]) => (
                  <div key={k} className="text-left">
                    <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                      <Term name={k}>{k}</Term>
                    </p>
                    <p className="font-mono text-xs font-semibold text-foreground">{(v * 100).toFixed(2)}%</p>
                  </div>
                ))}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}

// ── Main ─────────────────────────────────────────────────────────────────────

interface InsightPanelProps {
  insights: AgenticInsights;
  modelScores?: ModelFitResult[];
}

export function InsightPanel({ insights, modelScores = [] }: InsightPanelProps) {
  const allInsights = insights.insights ?? [];
  const allRecs = insights.recommendations ?? [];
  const leakageCols = insights.leakage_risk_columns ?? [];
  const highInsights = allInsights.filter((i) => i.severity === "high");
  const otherInsights = allInsights.filter((i) => i.severity !== "high");

  return (
    <div className="space-y-8">

      {/* AI summary */}
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
          AI Summary
        </p>
        <p className="text-sm leading-relaxed text-foreground/80 max-w-2xl">
          {insights.summary}
        </p>
      </div>

      {/* Recommendation chips */}
      {allRecs.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
            Recommended actions
          </p>
          <div className="flex flex-wrap gap-2">
            {allRecs.slice(0, 6).map((rec, i) => (
              <RecommendationChip key={i} rec={rec} />
            ))}
          </div>
          {allRecs.length > 6 && (
            <div className="mt-3 space-y-1.5 pl-0.5">
              {allRecs.slice(6).map((rec, i) => (
                <p key={i} className="text-xs text-muted-foreground flex items-start gap-2">
                  <span className="text-foreground/30 shrink-0 mt-0.5">→</span>
                  {rec.action}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Findings */}
      {(highInsights.length > 0 || otherInsights.length > 0) && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
            Findings
          </p>
          <div className="space-y-3">
            {[...highInsights, ...otherInsights].map((item, i) => (
              <FindingRow key={i} item={item} />
            ))}
          </div>
        </div>
      )}

      {/* Leakage risk */}
      {leakageCols.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
            <Term name="leakage">Leakage risk</Term>
          </p>
          <div className="flex flex-wrap gap-1.5">
            {leakageCols.map((col) => (
              <span key={col} className="rounded border border-red-300/40 bg-red-500/8 px-2 py-0.5 font-mono text-[11px] text-red-600 dark:text-red-400">
                {col}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Model scores */}
      {modelScores.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
            Model scores — <Term name="cross-validation">3-fold CV</Term>
          </p>
          <ModelScoresPanel scores={modelScores} />
        </div>
      )}
    </div>
  );
}

function RecommendationChip({ rec }: { rec: Recommendation }) {
  const [open, setOpen] = useState(false);
  return (
    <button
      onClick={() => setOpen((v) => !v)}
      className={cn(
        "rounded border px-3 py-1.5 text-xs font-medium transition-all text-left",
        open
          ? "border-foreground/30 bg-secondary text-foreground"
          : "border-border text-muted-foreground hover:border-foreground/25 hover:text-foreground"
      )}
    >
      {open ? (
        <span className="block text-xs leading-relaxed">
          {rec.action}
          {rec.columns.length > 0 && (
            <span className="ml-1.5 font-mono text-[10px] opacity-60">
              ({rec.columns.slice(0, 3).join(", ")})
            </span>
          )}
        </span>
      ) : (
        <span>
          {rec.category.replace(/_/g, " ")}
          {rec.columns.length > 0 && (
            <span className="ml-1.5 font-mono text-[10px] opacity-50">
              {rec.columns[0]}{rec.columns.length > 1 ? ` +${rec.columns.length - 1}` : ""}
            </span>
          )}
        </span>
      )}
    </button>
  );
}

function FindingRow({ item }: { item: Insight }) {
  return (
    <div className="flex items-start gap-2.5">
      <SeverityDot severity={item.severity} />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-foreground/80 leading-relaxed">{item.message}</p>
        {item.columns.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {item.columns.slice(0, 5).map((col) => (
              <span key={col} className="font-mono text-[10px] text-muted-foreground bg-muted/60 rounded px-1.5 py-0.5">
                {col}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function InsightPanelSkeleton() {
  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-3 w-24" />
        <div className="flex gap-2 flex-wrap">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-32 rounded" />)}
        </div>
      </div>
    </div>
  );
}
