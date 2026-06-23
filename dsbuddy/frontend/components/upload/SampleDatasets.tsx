"use client";

import { useState } from "react";
import { FlaskConicalIcon, HomeIcon, UsersIcon, Loader2Icon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ProblemType } from "@/lib/types";

interface Sample {
  id: string;
  name: string;
  description: string;
  filename: string;
  rows: number;
  columns: number;
  targetColumn: string;
  problemType: ProblemType;
  domain: string;
  icon: React.ReactNode;
  color: string;
}

const SAMPLES: Sample[] = [
  {
    id: "titanic",
    name: "Titanic Survival",
    description: "Predict passenger survival based on class, age, fare, and gender.",
    filename: "titanic.csv",
    rows: 30,
    columns: 8,
    targetColumn: "survived",
    problemType: "classification",
    domain: "Other",
    icon: <FlaskConicalIcon className="h-4 w-4" />,
    color: "text-blue-500",
  },
  {
    id: "house_prices",
    name: "House Prices",
    description: "Predict property prices from size, location, and features.",
    filename: "house_prices.csv",
    rows: 30,
    columns: 8,
    targetColumn: "price",
    problemType: "regression",
    domain: "Real Estate",
    icon: <HomeIcon className="h-4 w-4" />,
    color: "text-emerald-500",
  },
  {
    id: "customer_churn",
    name: "Customer Churn",
    description: "Classify which customers are likely to cancel their subscription.",
    filename: "customer_churn.csv",
    rows: 30,
    columns: 8,
    targetColumn: "churn",
    problemType: "classification",
    domain: "E-commerce",
    icon: <UsersIcon className="h-4 w-4" />,
    color: "text-violet-500",
  },
];

interface SampleDatasetsProps {
  onSelect: (
    file: File,
    targetColumn: string,
    problemType: ProblemType,
    domain: string
  ) => void;
  disabled?: boolean;
}

export function SampleDatasets({ onSelect, disabled = false }: SampleDatasetsProps) {
  const [loadingId, setLoadingId] = useState<string | null>(null);

  async function handleClick(sample: Sample) {
    if (disabled || loadingId) return;
    setLoadingId(sample.id);
    try {
      const res = await fetch(`/samples/${sample.filename}`);
      const blob = await res.blob();
      const file = new File([blob], sample.filename, { type: "text/csv" });
      onSelect(file, sample.targetColumn, sample.problemType, sample.domain);
    } catch {
      // silently ignore — user can still upload manually
    } finally {
      setLoadingId(null);
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
        Or try a sample dataset
      </p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {SAMPLES.map((sample) => {
          const isLoading = loadingId === sample.id;
          return (
            <button
              key={sample.id}
              type="button"
              onClick={() => handleClick(sample)}
              disabled={disabled || !!loadingId}
              className={cn(
                "group relative flex flex-col gap-1.5 rounded-lg border border-border bg-muted/20 px-3 py-3 text-left transition-all",
                "hover:border-primary/40 hover:bg-muted/40 hover:shadow-sm",
                "disabled:cursor-not-allowed disabled:opacity-50",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              )}
            >
              <div className="flex items-center gap-2">
                <span className={cn("shrink-0", sample.color)}>
                  {isLoading ? (
                    <Loader2Icon className="h-4 w-4 animate-spin" />
                  ) : (
                    sample.icon
                  )}
                </span>
                <span className="text-xs font-semibold leading-tight">
                  {sample.name}
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-snug line-clamp-2">
                {sample.description}
              </p>
              <div className="flex flex-wrap gap-1 mt-0.5">
                <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-muted text-muted-foreground">
                  {sample.rows} rows
                </span>
                <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-muted text-muted-foreground">
                  target: {sample.targetColumn}
                </span>
                <span className={cn(
                  "inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium",
                  sample.problemType === "regression"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                )}>
                  {sample.problemType}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
