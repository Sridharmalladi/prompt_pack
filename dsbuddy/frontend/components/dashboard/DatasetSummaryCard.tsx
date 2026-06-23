"use client";

import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Term } from "@/components/Term";
import type { AnalyzeResponse } from "@/lib/types";

function StatRow({ label, value, highlight }: { label: string; value: ReactNode; highlight?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5 py-2 border-b border-border/40 last:border-0">
      <span className={`text-lg font-semibold leading-none tracking-tight ${highlight ? "text-amber-600 dark:text-amber-400" : "text-foreground"}`}>
        {value}
      </span>
      <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</span>
    </div>
  );
}

interface DatasetSummaryCardProps {
  result: AnalyzeResponse;
}

export function DatasetSummaryCard({ result }: DatasetSummaryCardProps) {
  const { file_info, profile } = result;

  const avgMissing = profile && profile.columns.length > 0
    ? profile.columns.reduce((s, c) => s + c.missing_pct, 0) / profile.columns.length
    : null;

  const numericCols = profile?.columns.filter((c) => c.mean !== null).length ?? 0;
  const catCols = (profile?.columns.length ?? 0) - numericCols;

  return (
    <div className="space-y-0">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3 truncate" title={file_info.filename}>
        {file_info.filename}
      </p>

      <StatRow label="rows" value={file_info.row_count.toLocaleString()} />
      <StatRow label="columns" value={file_info.column_count} />
      <StatRow label="numeric" value={numericCols} />
      <StatRow label="categorical" value={catCols} />

      {avgMissing !== null && (
        <StatRow
          label="avg missing"
          value={`${avgMissing.toFixed(1)}%`}
          highlight={avgMissing > 10}
        />
      )}

      <StatRow
        label="file size"
        value={`${(file_info.size_bytes / 1024).toFixed(0)} KB`}
      />

      {profile && profile.duplicate_count > 0 && (
        <StatRow
          label="duplicate rows"
          value={`${profile.duplicate_count} (${profile.duplicate_pct.toFixed(1)}%)`}
          highlight
        />
      )}

      {/* Constant columns */}
      {profile && profile.constant_columns.length > 0 && (
        <div className="pt-4 space-y-1">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Constant cols</p>
          <div className="flex flex-wrap gap-1">
            {profile.constant_columns.map((col) => (
              <span key={col} className="rounded bg-red-500/10 px-1.5 py-0.5 font-mono text-[9px] text-red-600 dark:text-red-400">
                {col}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Class distribution */}
      {profile?.class_distribution && (
        <div className="pt-4 space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Target classes
            {profile.class_distribution.imbalanced && (
              <span className="ml-1.5 text-amber-600 dark:text-amber-400">imbalanced</span>
            )}
          </p>
          {Object.entries(profile.class_distribution.counts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 6)
            .map(([cls, count]) => (
              <div key={cls} className="flex items-center justify-between gap-2">
                <span className="text-[11px] truncate text-foreground/70" title={cls}>{cls}</span>
                <span className="text-[11px] font-mono text-muted-foreground">{count.toLocaleString()}</span>
              </div>
            ))}
        </div>
      )}

      {/* Top correlations */}
      {profile?.top_correlations && profile.top_correlations.length > 0 && (
        <div className="pt-4 space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            <Term name="correlation">Top correlations</Term>
          </p>
          {profile.top_correlations.slice(0, 5).map((e) => (
            <div key={e.column} className="flex items-center justify-between gap-2">
              <span className="text-[11px] truncate text-foreground/70" title={e.column}>{e.column}</span>
              <span className={`text-[11px] font-mono ${Math.abs(e.correlation) > 0.5 ? "text-foreground font-semibold" : "text-muted-foreground"}`}>
                {e.correlation >= 0 ? "+" : ""}{e.correlation.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function DatasetSummaryCardSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-3 w-24" />
      {[80, 40, 40, 40, 50, 40].map((w, i) => (
        <div key={i} className="space-y-1">
          <Skeleton className={`h-5 w-${w}`} />
          <Skeleton className="h-2.5 w-16" />
        </div>
      ))}
    </div>
  );
}
