"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import dynamic from "next/dynamic";
import { useAppStore } from "@/lib/store";
import {
  DatasetSummaryCard,
  DatasetSummaryCardSkeleton,
} from "@/components/dashboard/DatasetSummaryCard";
import {
  InsightPanel,
  InsightPanelSkeleton,
} from "@/components/dashboard/InsightPanel";
import { MulticollinearityPanel } from "@/components/dashboard/MulticollinearityPanel";
import { DataPreviewTable } from "@/components/dashboard/DataPreviewTable";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeftIcon } from "lucide-react";
import { useAssist } from "@/lib/assist-context";
import type { AnalyzeResponse } from "@/lib/types";

const FeatureGraphView = dynamic(
  () => import("@/components/dashboard/FeatureGraphView").then((m) => ({ default: m.FeatureGraphView })),
  { ssr: false, loading: () => <Skeleton className="h-[400px] w-full rounded" /> }
);
const DistributionChart = dynamic(
  () => import("@/components/dashboard/DistributionChart").then((m) => ({ default: m.DistributionChart })),
  { ssr: false }
);
const CorrelationPanel = dynamic(
  () => import("@/components/dashboard/CorrelationPanel").then((m) => ({ default: m.CorrelationPanel })),
  { ssr: false }
);
const RiskHeatmap = dynamic(
  () => import("@/components/dashboard/RiskHeatmap").then((m) => ({ default: m.RiskHeatmap })),
  { ssr: false }
);
const ChatDrawer = dynamic(
  () => import("@/components/dashboard/ChatDrawer").then((m) => ({ default: m.ChatDrawer })),
  { ssr: false }
);

export default function DashboardPage() {
  const result = useAppStore((s) => s.result);
  const router = useRouter();
  const { on: assistOn, toggle: toggleAssist } = useAssist();

  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);
  useEffect(() => {
    if (hydrated && !result) router.replace("/upload");
  }, [hydrated, result, router]);

  if (!hydrated || !result) return <DashboardSkeleton />;

  const { file_info, profile } = result;

  return (
    <div className="min-h-screen bg-background flex flex-col">

      {/* ── Nav ── */}
      <nav className="flex items-center gap-4 px-8 py-4 border-b border-border/60 sticky top-0 z-30 bg-background/95 backdrop-blur-sm">
        <Link
          href="/upload"
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeftIcon className="h-3 w-3" />
          <Image src="/logo.png" alt="" width={18} height={18} className="rounded" />
          dsbuddy
        </Link>

        <span className="text-border/80">·</span>

        <span className="text-xs font-medium text-foreground truncate max-w-[200px]" title={file_info.filename}>
          {file_info.filename}
        </span>

        {profile && (
          <>
            <span className="text-border/80">·</span>
            <span className="text-xs text-muted-foreground">
              {file_info.row_count.toLocaleString()} rows · {file_info.column_count} cols
            </span>
          </>
        )}

        <div className="ml-auto flex items-center gap-3">
          {result.insights && (
            <span className="text-[10px] font-medium text-green-700 dark:text-green-400 bg-green-500/10 rounded px-2 py-1">
              Analysis ready
            </span>
          )}
          <button
            onClick={toggleAssist}
            className={`text-xs font-medium px-3 py-1.5 rounded border transition-all ${
              assistOn
                ? "bg-foreground text-background border-foreground"
                : "border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground"
            }`}
          >
            ✦ Assist
          </button>
          <ThemeToggle />
        </div>
      </nav>

      {/* ── Body ── */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[200px_1fr_220px] divide-x divide-border/50">

        {/* ── Left sidebar — dataset numbers ── */}
        <aside className="hidden lg:block p-6 space-y-6">
          <ErrorBoundary label="Dataset summary">
            <DatasetSummaryCard result={result} />
          </ErrorBoundary>
        </aside>

        {/* ── Center — insights + charts ── */}
        <main className="min-w-0 p-6 lg:p-8 space-y-8">

          {/* Data preview */}
          <ErrorBoundary label="Data preview">
            {result.preview_rows.length > 0 && result.profile && (
              <DataPreviewTable
                rows={result.preview_rows}
                columns={result.profile.columns}
                semanticLabels={result.semantic_labels}
              />
            )}
          </ErrorBoundary>

          {/* AI insights */}
          <ErrorBoundary label="AI insights">
            {result.insights ? (
              <InsightPanel insights={result.insights} modelScores={result.model_scores} />
            ) : (
              <div className="rounded border border-dashed border-border/60 p-10 text-center text-xs text-muted-foreground">
                No AI insights — check the backend logs.
              </div>
            )}
          </ErrorBoundary>

          {/* Multicollinearity */}
          <ErrorBoundary label="Multicollinearity">
            {result.graph && <MulticollinearityPanel graph={result.graph} />}
          </ErrorBoundary>

          {/* Feature graph */}
          <div className="hidden md:block">
            <ErrorBoundary label="Feature graph">
              <FeatureGraphView result={result} />
            </ErrorBoundary>
          </div>

          {/* Correlation */}
          <ErrorBoundary label="Correlation chart">
            {result.profile && <CorrelationPanel result={result} />}
          </ErrorBoundary>

          {/* Distributions */}
          <ErrorBoundary label="Distribution charts">
            {result.profile && <DistributionChart result={result} />}
          </ErrorBoundary>

          {/* Risk heatmap */}
          <ErrorBoundary label="Risk heatmap">
            {result.insights && <RiskHeatmap insights={result.insights} />}
          </ErrorBoundary>
        </main>

        {/* ── Right sidebar — spotlight stats ── */}
        <aside className="hidden lg:block p-6">
          <ErrorBoundary label="Profile summary">
            <ProfileSummaryAside result={result} />
          </ErrorBoundary>
        </aside>
      </div>

      <ChatDrawer result={result} />
    </div>
  );
}

// ── Right sidebar ─────────────────────────────────────────────────────────────

function ProfileSummaryAside({ result }: { result: AnalyzeResponse }) {
  const profile = result.profile;
  if (!profile) return null;

  const highMissing = profile.columns
    .filter((c) => c.missing_pct > 5)
    .sort((a, b) => b.missing_pct - a.missing_pct)
    .slice(0, 8);

  const highSkew = profile.columns
    .filter((c) => c.skew !== null && Math.abs(c.skew) > 1)
    .sort((a, b) => Math.abs(b.skew ?? 0) - Math.abs(a.skew ?? 0))
    .slice(0, 6);

  const modelScores = result.model_scores ?? [];

  return (
    <div className="space-y-8">

      {/* Model scores */}
      {modelScores.length > 0 && (
        <section>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
            Model scores
          </p>
          <div className="space-y-2.5">
            {modelScores.map((m) => {
              const primary = Object.entries(m.metrics)[0];
              return (
                <div key={m.model_name} className="space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-foreground truncate">{m.model_name}</span>
                    {primary && !m.error && (
                      <span className="text-xs font-mono font-semibold text-foreground shrink-0">
                        {(primary[1] * 100).toFixed(0)}%
                      </span>
                    )}
                    {m.error && <span className="text-[10px] text-muted-foreground">—</span>}
                  </div>
                  {!m.error && primary && (
                    <div className="h-0.5 w-full bg-border rounded-full overflow-hidden">
                      <div
                        className="h-full bg-foreground/70 rounded-full transition-all duration-700"
                        style={{ width: `${Math.max(0, Math.min(100, primary[1] * 100))}%` }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Missing */}
      {highMissing.length > 0 && (
        <section>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
            High missingness
          </p>
          <div className="space-y-2">
            {highMissing.map((c) => (
              <div key={c.name} className="flex items-center justify-between gap-2">
                <span className="text-xs text-foreground/80 truncate">{c.name}</span>
                <span className={`text-xs font-mono ${c.missing_pct > 30 ? "text-red-500" : "text-muted-foreground"}`}>
                  {c.missing_pct.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Skewness */}
      {highSkew.length > 0 && (
        <section>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
            High skewness
          </p>
          <div className="space-y-2">
            {highSkew.map((c) => (
              <div key={c.name} className="flex items-center justify-between gap-2">
                <span className="text-xs text-foreground/80 truncate">{c.name}</span>
                <span className="text-xs font-mono text-muted-foreground">
                  {(c.skew ?? 0) > 0 ? "+" : ""}{(c.skew ?? 0).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ── Loading skeleton ──────────────────────────────────────────────────────────

function DashboardSkeleton() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <nav className="flex items-center gap-4 px-8 py-4 border-b border-border/60">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-4" />
        <Skeleton className="h-4 w-32" />
        <div className="ml-auto flex gap-3">
          <Skeleton className="h-7 w-24 rounded" />
          <Skeleton className="h-7 w-7 rounded" />
        </div>
      </nav>
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[200px_1fr_220px] divide-x divide-border/50">
        <aside className="hidden lg:block p-6">
          <DatasetSummaryCardSkeleton />
        </aside>
        <main className="p-8 space-y-8">
          <InsightPanelSkeleton />
          <Skeleton className="h-[400px] w-full rounded" />
        </main>
        <aside className="hidden lg:block p-6 space-y-4">
          <Skeleton className="h-4 w-20" />
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
        </aside>
      </div>
    </div>
  );
}
