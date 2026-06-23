"use client";

import type { FeatureGraph } from "@/lib/types";
import { Term } from "@/components/Term";

interface Props {
  graph: FeatureGraph;
}

export function MulticollinearityPanel({ graph }: Props) {
  const clusters = graph.multicollinearity_clusters;

  if (clusters.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-4">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <Term name="multicollinearity">Multicollinearity</Term>
        </p>
        <p className="text-xs text-green-600 dark:text-green-400">
          ✓ No highly correlated column groups detected
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <Term name="multicollinearity">Multicollinearity</Term> Clusters
        </p>
        <span className="rounded-full bg-yellow-500/10 px-2 py-0.5 text-[10px] font-medium text-yellow-600 dark:text-yellow-400">
          {clusters.length} {clusters.length === 1 ? "group" : "groups"}
        </span>
      </div>
      <p className="text-xs text-muted-foreground">
        These column groups are highly correlated with each other. Consider keeping just one from each group before training.
      </p>
      <div className="space-y-2">
        {clusters.map((cluster, i) => (
          <div key={i} className="rounded-md border border-yellow-500/20 bg-yellow-500/5 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-yellow-600 dark:text-yellow-400">
                Group {i + 1}
              </span>
              <span className="text-[10px] text-muted-foreground">
                max <Term name="correlation">corr</Term> {cluster.max_correlation.toFixed(2)}
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {cluster.columns.map((col) => (
                <span
                  key={col}
                  className="rounded bg-yellow-500/10 px-2 py-0.5 font-mono text-[10px] text-yellow-700 dark:text-yellow-300"
                >
                  {col}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
