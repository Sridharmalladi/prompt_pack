import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RiskSeverity } from "@/lib/types";

const SEVERITY_CONFIG: Record<RiskSeverity, { label: string; className: string }> = {
  low: {
    label: "Low",
    className:
      "border-green-200 bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800",
  },
  medium: {
    label: "Medium",
    className:
      "border-yellow-200 bg-yellow-50 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800",
  },
  high: {
    label: "High",
    className:
      "border-red-200 bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800",
  },
};

interface RiskBadgeProps {
  severity: RiskSeverity;
  className?: string;
}

export function RiskBadge({ severity, className }: RiskBadgeProps) {
  const { label, className: severityClass } = SEVERITY_CONFIG[severity];
  return (
    <Badge
      variant="outline"
      className={cn("text-[10px] font-semibold shrink-0", severityClass, className)}
    >
      {label}
    </Badge>
  );
}
