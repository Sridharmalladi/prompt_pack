"use client";

import { CheckIcon, LoaderIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { UploadStep } from "@/lib/types";

const STEPS: { key: UploadStep; label: string; desc: string }[] = [
  { key: "scanning",  label: "Labeling columns",   desc: "Semantic types" },
  { key: "profiling", label: "Statistics",          desc: "200+ measures" },
  { key: "graph",     label: "Feature graph",       desc: "Relationships" },
  { key: "training",  label: "Training models",     desc: "Real CV scores" },
  { key: "reasoning", label: "Claude reasoning",    desc: "AI insights" },
  { key: "done",      label: "Done",                desc: "Ready" },
];

const STEP_ORDER: UploadStep[] = [
  "uploading",
  "scanning",
  "profiling",
  "graph",
  "training",
  "reasoning",
  "done",
];

function stepIndex(step: UploadStep): number {
  const i = STEP_ORDER.indexOf(step);
  return i === -1 ? 0 : i;
}

interface ProgressStepperProps {
  currentStep: UploadStep;
  message?: string;
}

export function ProgressStepper({ currentStep, message }: ProgressStepperProps) {
  if (currentStep === "idle" || currentStep === "error") return null;

  const currentIdx = stepIndex(currentStep);
  const isDone = currentStep === "done";

  return (
    <div className="w-full space-y-4">
      {/* Steps list */}
      <div className="space-y-2">
        {STEPS.map((step, idx) => {
          const stepIdx = idx + 1; // offset by 1 since STEP_ORDER[0]=uploading
          const done = stepIdx < currentIdx || isDone;
          const active = stepIdx === currentIdx && !isDone;
          const pending = stepIdx > currentIdx && !isDone;

          return (
            <div
              key={step.key}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 transition-all duration-300",
                done && "opacity-100",
                active && "bg-blue-500/5 border border-blue-500/20",
                pending && "opacity-40"
              )}
              style={{
                animation: active ? "slideUp 0.3s ease-out" : undefined,
              }}
            >
              {/* Icon */}
              <div
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-full transition-all duration-500",
                  done && "bg-green-500 text-white scale-110",
                  active && "border-2 border-blue-500 bg-blue-500/10 text-blue-500",
                  pending && "border-2 border-muted-foreground/20 text-muted-foreground/40"
                )}
              >
                {done ? (
                  <CheckIcon
                    className="h-3 w-3"
                    style={{ animation: done ? "checkIn 0.4s cubic-bezier(.17,.67,.5,1.5)" : undefined }}
                  />
                ) : active ? (
                  <LoaderIcon className="h-3 w-3 animate-spin" />
                ) : (
                  <span className="text-[9px] font-semibold">{idx + 1}</span>
                )}
              </div>

              {/* Label */}
              <div className="flex-1 min-w-0">
                <p
                  className={cn(
                    "text-xs font-medium",
                    done && "text-green-600 dark:text-green-400",
                    active && "text-blue-600 dark:text-blue-400",
                    pending && "text-muted-foreground"
                  )}
                >
                  {step.label}
                </p>
                <p className="text-[10px] text-muted-foreground/60">{step.desc}</p>
              </div>

              {done && (
                <span className="text-[10px] font-medium text-green-600 dark:text-green-400">
                  done
                </span>
              )}
              {active && (
                <span className="text-[10px] text-blue-500 animate-pulse">running</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Live message */}
      {message && !isDone && (
        <p className="text-center text-[11px] text-muted-foreground animate-pulse">
          {message}
        </p>
      )}
    </div>
  );
}
