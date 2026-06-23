"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { AnalyzeResponse, ColumnProfile } from "@/lib/types";

// ── Data helpers ───────────────────────────────────────────────────────────────

interface ChartBar {
  label: string;
  value: number;
}

function topValuesData(top_values: Record<string, number>): ChartBar[] {
  return Object.entries(top_values)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8)
    .map(([label, value]) => ({
      label: label.length > 8 ? label.slice(0, 7) + "…" : label,
      value,
    }));
}

function gaussianData(mean: number, std: number): ChartBar[] {
  if (std <= 0) return [];
  const numBins = 14;
  return Array.from({ length: numBins }, (_, i) => {
    const z = -3 + (6 * i) / (numBins - 1);
    const x = mean + z * std;
    const value = Math.exp(-0.5 * z * z) * 100;
    return { label: x.toFixed(1), value };
  });
}

function buildChartData(col: ColumnProfile): ChartBar[] | null {
  if (col.top_values && Object.keys(col.top_values).length > 0) {
    return topValuesData(col.top_values);
  }
  if (col.mean !== null && col.std !== null) {
    return gaussianData(col.mean, col.std);
  }
  return null;
}

// ── Single feature mini-chart ──────────────────────────────────────────────────

interface MiniChartProps {
  col: ColumnProfile;
  isNumeric: boolean;
  isSelected: boolean;
  onClick: () => void;
}

function MiniChart({ col, isNumeric, isSelected, onClick }: MiniChartProps) {
  const data = buildChartData(col);
  const barColor = isSelected ? "hsl(217 91% 60%)" : "hsl(217 91% 60% / 0.5)";

  return (
    <Card
      onClick={onClick}
      className={cn(
        "cursor-pointer transition-all hover:shadow-md",
        isSelected && "ring-2 ring-ring"
      )}
    >
      <CardHeader className="pb-1 pt-3 px-3">
        <div className="flex items-start justify-between gap-1">
          <CardTitle
            className="text-[10px] font-semibold truncate leading-tight"
            title={col.name}
          >
            {col.name}
          </CardTitle>
          <Badge
            variant="secondary"
            className="text-[8px] px-1 py-0 h-4 shrink-0"
          >
            {isNumeric ? "num" : "cat"}
          </Badge>
        </div>
        <p className="text-[9px] text-muted-foreground">
          {col.missing_pct.toFixed(1)}% missing
          {col.mean !== null && ` · μ ${col.mean.toFixed(2)}`}
        </p>
      </CardHeader>
      <CardContent className="px-2 pb-2">
        {data ? (
          <ResponsiveContainer width="100%" height={80}>
            <BarChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
              <XAxis
                dataKey="label"
                tick={false}
                axisLine={false}
                tickLine={false}
              />
              <YAxis hide />
              <Tooltip
                contentStyle={{
                  fontSize: "10px",
                  padding: "4px 8px",
                  borderRadius: "6px",
                }}
                formatter={(v) => [typeof v === "number" ? v.toFixed(0) : v, ""]}
                labelStyle={{ fontSize: "10px" }}
              />
              <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                {data.map((_, idx) => (
                  <Cell key={idx} fill={barColor} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-20 flex items-center justify-center text-[10px] text-muted-foreground">
            No distribution data
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface DistributionChartProps {
  result: AnalyzeResponse;
}

export function DistributionChart({ result }: DistributionChartProps) {
  const selectedFeature = useAppStore((s) => s.selectedFeature);
  const setSelectedFeature = useAppStore((s) => s.setSelectedFeature);

  if (!result.profile) return null;

  // Pick top 6 by mutual info score, or fall back to first 6 profiled columns
  const rankedNames = result.profile.mutual_info.length > 0
    ? [...result.profile.mutual_info]
        .sort((a, b) => b.score - a.score)
        .slice(0, 6)
        .map((m) => m.column)
    : result.profile.columns.slice(0, 6).map((c) => c.name);

  const cols = rankedNames
    .map((name) => result.profile!.columns.find((c) => c.name === name))
    .filter((c): c is ColumnProfile => c !== undefined);

  if (cols.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Feature distributions</h3>
        <p className="text-[10px] text-muted-foreground">
          Top {cols.length} by mutual information · click to highlight
        </p>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {cols.map((col) => {
          const isNumeric = col.mean !== null;
          return (
            <MiniChart
              key={col.name}
              col={col}
              isNumeric={isNumeric}
              isSelected={selectedFeature === col.name}
              onClick={() =>
                setSelectedFeature(
                  selectedFeature === col.name ? null : col.name
                )
              }
            />
          );
        })}
      </div>
    </div>
  );
}
