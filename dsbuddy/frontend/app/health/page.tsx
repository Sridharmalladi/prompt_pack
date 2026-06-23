"use client";

import { useQuery } from "@tanstack/react-query";
import { checkHealth } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function HealthPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: checkHealth,
    refetchInterval: 10_000,
  });

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-lg">Backend connectivity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              http://localhost:8000/health
            </span>
            {isLoading && <Skeleton className="h-5 w-16" />}
            {isError && (
              <Badge variant="destructive">Unreachable</Badge>
            )}
            {data && (
              <Badge
                variant={data.status === "ok" ? "default" : "secondary"}
                className={
                  data.status === "ok"
                    ? "bg-green-500 hover:bg-green-600"
                    : ""
                }
              >
                {data.status}
              </Badge>
            )}
          </div>

          {isError && (
            <p className="text-xs text-destructive">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          )}

          {data && (
            <pre className="text-xs bg-muted rounded p-2 overflow-auto">
              {JSON.stringify(data, null, 2)}
            </pre>
          )}

          <p className="text-xs text-muted-foreground">
            Auto-refreshes every 10 s
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
