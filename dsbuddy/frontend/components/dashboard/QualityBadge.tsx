import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type QualityTier = "excellent" | "good" | "fair" | "poor" | "unknown";

const TIER_CONFIG: Record<
  QualityTier,
  { label: string; className: string }
> = {
  excellent: {
    label: "Excellent",
    className: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400",
  },
  good: {
    label: "Good",
    className: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400",
  },
  fair: {
    label: "Fair",
    className: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400",
  },
  poor: {
    label: "Poor",
    className: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400",
  },
  unknown: {
    label: "Unknown",
    className: "bg-muted text-muted-foreground",
  },
};

interface QualityBadgeProps {
  tier: QualityTier;
  className?: string;
}

export function QualityBadge({ tier, className }: QualityBadgeProps) {
  const { label, className: tierClass } = TIER_CONFIG[tier];
  return (
    <Badge
      variant="outline"
      className={cn("font-medium", tierClass, className)}
    >
      {label}
    </Badge>
  );
}

export function deriveQualityTier(avgMissingPct: number): QualityTier {
  if (avgMissingPct < 1) return "excellent";
  if (avgMissingPct < 5) return "good";
  if (avgMissingPct < 15) return "fair";
  return "poor";
}
