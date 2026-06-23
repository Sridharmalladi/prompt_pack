"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalyzeResponse } from "@/lib/types";

interface CorrelationPanelProps {
  result: AnalyzeResponse;
}

interface TooltipProps {
  active?: boolean;
  payload?: { value: number; payload: { column: string; correlation: number } }[];
}

function CorrelationTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const { column, correlation } = payload[0].payload;
  const corr = correlation ?? 0;
  return (
    <div className="rounded-md border border-border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="font-semibold">{column}</p>
      <p className={`font-mono mt-0.5 ${corr >= 0 ? "text-blue-600 dark:text-blue-400" : "text-orange-600 dark:text-orange-400"}`}>
        r = {corr >= 0 ? "+" : ""}{corr.toFixed(4)}
      </p>
    </div>
  );
}

export function CorrelationPanel({ result }: CorrelationPanelProps) {
  const correlations = result.profile?.top_correlations ?? [];
  if (correlations.length === 0) return null;

  const data = [...correlations]
    .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
    .slice(0, 10)
    .map((e) => ({ column: e.column, correlation: e.correlation }));

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">
            Correlations with target
          </CardTitle>
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-3 rounded-sm bg-blue-500" />
              Positive
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-3 rounded-sm bg-orange-500" />
              Negative
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0 pb-4">
        <ResponsiveContainer width="100%" height={data.length * 32 + 20}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 48, bottom: 0, left: 8 }}
            barCategoryGap="25%"
          >
            <XAxis
              type="number"
              domain={[-1, 1]}
              tickCount={5}
              tickFormatter={(v) => v.toFixed(1)}
              tick={{ fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="column"
              width={90}
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CorrelationTooltip />} cursor={{ fill: "hsl(var(--muted)/0.3)" }} />
            <ReferenceLine x={0} stroke="hsl(var(--border))" strokeWidth={1} />
            <Bar dataKey="correlation" radius={[0, 3, 3, 0]} maxBarSize={18}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.correlation >= 0 ? "hsl(217 91% 60%)" : "hsl(25 95% 53%)"}
                  fillOpacity={0.7 + Math.abs(entry.correlation) * 0.3}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
