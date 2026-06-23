"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { analyzeDatasetStream } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import type { ProblemType, UploadStep } from "@/lib/types";
import { DropZone } from "@/components/upload/DropZone";
import { ProgressStepper } from "@/components/upload/ProgressStepper";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircleIcon, Loader2Icon } from "lucide-react";
import Image from "next/image";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";

const SSE_STEP_MAP: Record<string, UploadStep> = {
  scanning: "scanning", scanning_done: "scanning",
  profiling: "profiling", profiling_done: "profiling",
  graph: "graph", graph_done: "graph",
  training: "training", training_done: "training",
  reasoning: "reasoning",
  done: "done", error: "error",
};

const PROBLEM_TYPES: { value: ProblemType; label: string }[] = [
  { value: "classification", label: "Classification" },
  { value: "regression", label: "Regression" },
  { value: "clustering", label: "Clustering" },
  { value: "unknown", label: "Let it decide" },
];

const SAMPLES = [
  { id: "spotify", name: "Spotify Tracks 2024",      tag: "Classification", filename: "spotify_tracks_2024.csv",    target: "hit",       type: "classification" as ProblemType, domain: "Music" },
  { id: "nba",     name: "NBA Player Stats 2023-24", tag: "Regression",     filename: "nba_stats_2024.csv",          target: "salary_millions", type: "regression" as ProblemType,     domain: "Sports" },
  { id: "mh",      name: "Mental Health in Tech",    tag: "Classification", filename: "mental_health_tech_2023.csv", target: "treatment", type: "classification" as ProblemType, domain: "Healthcare" },
];

export default function UploadPage() {
  const router = useRouter();
  const { setResult, setUploadStep, uploadStep } = useAppStore();

  const [file, setFile] = useState<File | null>(null);
  const [targetColumn, setTargetColumn] = useState("");
  const [problemType, setProblemType] = useState<ProblemType>("unknown");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [liveMessage, setLiveMessage] = useState("");
  const [loadingSample, setLoadingSample] = useState<string | null>(null);

  const runAnalysis = useCallback(
    async (f: File, target: string, ptype: ProblemType, domain: string) => {
      setIsRunning(true);
      setErrorMessage(null);
      setLiveMessage("");
      setUploadStep("uploading");
      try {
        for await (const event of analyzeDatasetStream(f, target, ptype, domain || undefined)) {
          if (event.step === "done") {
            setUploadStep("done");
            setResult(event.data, `session_${Date.now()}`);
            router.push("/dashboard");
            return;
          } else if (event.step === "error") {
            setErrorMessage(event.message || "Analysis failed.");
            setUploadStep("error");
            return;
          } else {
            setUploadStep(SSE_STEP_MAP[event.step] ?? "uploading");
            setLiveMessage(event.message ?? "");
          }
        }
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "Something went wrong. Is the backend running?");
        setUploadStep("error");
      } finally {
        setIsRunning(false);
      }
    },
    [router, setResult, setUploadStep]
  );

  async function handleSampleClick(sample: typeof SAMPLES[0]) {
    if (isRunning || loadingSample) return;
    setLoadingSample(sample.id);
    try {
      const res = await fetch(`/samples/${sample.filename}`);
      const blob = await res.blob();
      const f = new File([blob], sample.filename, { type: "text/csv" });
      setFile(f);
      setTargetColumn(sample.target);
      setProblemType(sample.type);
      runAnalysis(f, sample.target, sample.type, sample.domain);
    } catch {
      setErrorMessage("Could not load sample file.");
    } finally {
      setLoadingSample(null);
    }
  }

  const canSubmit = file !== null && targetColumn.trim() !== "" && !isRunning;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    runAnalysis(file!, targetColumn, problemType, "");
  }

  const showProgress = uploadStep !== "idle" && uploadStep !== "error";

  return (
    <div className="min-h-screen bg-background flex flex-col">

      {/* ── Nav ── */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-border/60">
        <div className="flex items-center gap-2">
          <Image src="/logo.png" alt="" width={22} height={22} className="rounded" />
          <span className="text-sm font-semibold tracking-tight text-foreground/80">dsbuddy</span>
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <button
            onClick={() => document.getElementById("upload-form")?.scrollIntoView({ behavior: "smooth" })}
            className="rounded-md bg-foreground px-4 py-1.5 text-xs font-medium text-background hover:opacity-80 transition-opacity"
          >
            Get started
          </button>
        </div>
      </nav>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col lg:flex-row">

        {/* Left — hero */}
        <div className="lg:w-[52%] flex flex-col justify-center px-10 py-16 lg:px-16 lg:py-20 border-r border-border/50">
          <h1 className="text-5xl lg:text-6xl font-bold leading-[1.08] tracking-tight text-foreground mb-6">
            Your data has<br />a story.<br />
            <span className="text-foreground/50">Let&apos;s read it<br />together.</span>
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
            Drop a CSV and get back something worth reading — field summaries, real risk flags, trained models, and a clear view of what matters before you touch any code.
          </p>

          {/* Stats row */}
          <div className="mt-16 flex items-center gap-10 border-t border-border/60 pt-8">
            {[
              { n: "200+", label: "statistics" },
              { n: "< 10s", label: "turnaround" },
              { n: "2 LLM passes", label: "per upload" },
              { n: "Zero setup", label: "needed" },
            ].map(({ n, label }) => (
              <div key={n}>
                <p className="text-sm font-semibold text-foreground">{n}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right — form */}
        <div className="lg:w-[48%] flex flex-col justify-center px-8 py-12 lg:px-12" id="upload-form">
          <form onSubmit={handleSubmit} className="space-y-5 max-w-md w-full mx-auto">

            {/* Drop zone */}
            <DropZone
              file={file}
              onFileSelect={setFile}
              onFileClear={() => { setFile(null); setUploadStep("idle"); }}
              disabled={isRunning}
            />

            {/* Target column */}
            <div className="space-y-1.5">
              <Label htmlFor="target" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Target column <span className="text-destructive">*</span>
              </Label>
              <Input
                id="target"
                placeholder="e.g. survived, price, churn"
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                disabled={isRunning}
                className="bg-card border-border/70 text-sm"
              />
            </div>

            {/* Problem type */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Task type
              </Label>
              <div className="flex gap-1.5 flex-wrap">
                {PROBLEM_TYPES.map(({ value, label }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setProblemType(value)}
                    disabled={isRunning}
                    className={cn(
                      "rounded px-3 py-1.5 text-xs font-medium transition-all border",
                      problemType === value
                        ? "bg-foreground text-background border-foreground"
                        : "border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground bg-transparent"
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Progress */}
            {showProgress && (
              <div className="rounded-lg border border-border/60 bg-card p-4">
                <ProgressStepper currentStep={uploadStep} message={liveMessage} />
              </div>
            )}

            {/* Error */}
            {errorMessage && (
              <div className="flex items-start gap-2 rounded border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
                <AlertCircleIcon className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                {errorMessage}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={!canSubmit}
              className="w-full rounded bg-foreground py-2.5 text-sm font-medium text-background hover:opacity-80 transition-opacity disabled:opacity-30 flex items-center justify-center gap-2"
            >
              {isRunning && <Loader2Icon className="h-4 w-4 animate-spin" />}
              {isRunning ? "Analysing…" : "Analyse dataset"}
            </button>
          </form>

          {/* Sample datasets */}
          {!isRunning && !file && (
            <div className="mt-8 max-w-md w-full mx-auto">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
                Or start with a sample
              </p>
              <div className="flex gap-2 flex-wrap">
                {SAMPLES.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => handleSampleClick(s)}
                    disabled={!!loadingSample || isRunning}
                    className={cn(
                      "rounded border border-border bg-card px-3.5 py-2.5 text-left transition-all hover:border-foreground/30 hover:bg-secondary disabled:opacity-40",
                      loadingSample === s.id && "opacity-50"
                    )}
                  >
                    <p className="text-xs font-semibold text-foreground leading-tight">{s.name}</p>
                    <p className={cn(
                      "mt-1 text-[10px] font-medium",
                      s.type === "regression" ? "text-emerald-600 dark:text-emerald-400" : "text-blue-600 dark:text-blue-400"
                    )}>
                      {s.tag}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
