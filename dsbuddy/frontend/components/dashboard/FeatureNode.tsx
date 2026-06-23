"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
export type FeatureNodeData = {
  name: string;
  importance: number;
  semantic_label: string | null;
};

const IMPORTANCE_STYLES = {
  high: "bg-green-50 border-green-400 text-green-900 dark:bg-green-900/30 dark:border-green-600 dark:text-green-200",
  medium: "bg-yellow-50 border-yellow-400 text-yellow-900 dark:bg-yellow-900/30 dark:border-yellow-600 dark:text-yellow-200",
  low: "bg-muted border-border text-muted-foreground",
};

// Lowercase labels the semantic scanner actually returns
const SEMANTIC_BADGE_STYLES: Record<string, string> = {
  leakage: "bg-red-100 text-red-800 border-red-300 dark:bg-red-900/30 dark:text-red-400",
  identifier: "bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-900/30 dark:text-purple-400",
  date: "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400",
  age: "bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/30 dark:text-orange-400",
  monetary_amount: "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-400",
  geographic: "bg-teal-100 text-teal-800 border-teal-300 dark:bg-teal-900/30 dark:text-teal-400",
  percentage: "bg-cyan-100 text-cyan-800 border-cyan-300 dark:bg-cyan-900/30 dark:text-cyan-400",
};

// Labels that add no visual signal — suppress the badge
const SILENT_LABELS = new Set(["unknown", "category", "score", "boolean", "free_text"]);

function importanceTier(score: number): keyof typeof IMPORTANCE_STYLES {
  if (score > 0.6) return "high";
  if (score > 0.3) return "medium";
  return "low";
}

export function FeatureNode({ data, selected }: NodeProps & { data: FeatureNodeData }) {
  const setSelectedFeature = useAppStore((s) => s.setSelectedFeature);
  const tier = importanceTier(data.importance);
  const showBadge = data.semantic_label !== null && !SILENT_LABELS.has(data.semantic_label);

  return (
    <div
      onClick={() => setSelectedFeature(data.name)}
      className={cn(
        "rounded-md border-2 px-3 py-1.5 cursor-pointer transition-all min-w-[80px] max-w-[140px]",
        IMPORTANCE_STYLES[tier],
        selected && "ring-2 ring-ring ring-offset-1"
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-border" />

      <p
        className="text-[10px] font-semibold truncate leading-tight"
        title={data.name}
      >
        {data.name}
      </p>

      <p className="text-[9px] opacity-60 leading-none mt-0.5">
        {(data.importance * 100).toFixed(0)}% imp.
      </p>

      {showBadge && (
        <Badge
          variant="outline"
          className={cn(
            "text-[8px] px-1 py-0 mt-1 h-4 leading-none",
            data.semantic_label && SEMANTIC_BADGE_STYLES[data.semantic_label]
          )}
        >
          {data.semantic_label}
        </Badge>
      )}

      <Handle type="source" position={Position.Right} className="!bg-border" />
    </div>
  );
}
