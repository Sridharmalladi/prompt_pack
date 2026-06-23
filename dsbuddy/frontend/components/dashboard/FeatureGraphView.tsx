"use client";

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type NodeTypes,
  useNodesState,
  useEdgesState,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/lib/store";
import { FeatureNode, type FeatureNodeData } from "./FeatureNode";
import type { AnalyzeResponse } from "@/lib/types";

const NODE_TYPES: NodeTypes = { feature: FeatureNode };

// ── Layout helpers ─────────────────────────────────────────────────────────────

function circularLayout(
  count: number,
  cx = 400,
  cy = 250,
  rx = 320,
  ry = 200
): { x: number; y: number }[] {
  return Array.from({ length: count }, (_, i) => {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2;
    return { x: cx + rx * Math.cos(angle), y: cy + ry * Math.sin(angle) };
  });
}

// ── Node details panel ────────────────────────────────────────────────────────

interface NodeDetailPanelProps {
  name: string;
  result: AnalyzeResponse;
  onClose: () => void;
}

function NodeDetailPanel({ name, result, onClose }: NodeDetailPanelProps) {
  const profileCol = result.profile?.columns.find((c) => c.name === name);
  const semanticLabel = result.semantic_labels?.[name] ?? null;
  const miScores = result.profile?.mutual_info ?? [];
  const maxMI = miScores.length > 0 ? Math.max(...miScores.map((m) => m.score)) : 1;
  const rawMI = miScores.find((m) => m.column === name)?.score ?? null;
  const importance = rawMI !== null && maxMI > 0 ? rawMI / maxMI : null;

  return (
    <Card className="w-64 shadow-lg">
      <CardHeader className="pb-2 pt-3 px-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-xs font-semibold break-all leading-snug">
            {name}
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5 shrink-0"
            onClick={onClose}
          >
            <XIcon className="h-3 w-3" />
          </Button>
        </div>
        {semanticLabel && semanticLabel !== "unknown" && (
          <Badge variant="secondary" className="text-[9px] w-fit mt-1">
            {semanticLabel}
          </Badge>
        )}
      </CardHeader>

      <CardContent className="px-3 pb-3 space-y-2">
        {importance !== null && (
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Importance</span>
            <span className="font-medium">
              {(importance * 100).toFixed(1)}%
            </span>
          </div>
        )}

        {profileCol && (
          <>
            <Separator />
            <div className="space-y-1.5">
              {[
                { label: "Type", value: profileCol.dtype },
                {
                  label: "Missing",
                  value: `${profileCol.missing_pct.toFixed(1)}%`,
                },
                ...(profileCol.mean !== null
                  ? [{ label: "Mean", value: profileCol.mean.toFixed(3) }]
                  : []),
                ...(profileCol.std !== null
                  ? [{ label: "Std", value: profileCol.std.toFixed(3) }]
                  : []),
                ...(profileCol.skew !== null
                  ? [{ label: "Skew", value: profileCol.skew.toFixed(3) }]
                  : []),
                ...(profileCol.outlier_count !== null
                  ? [
                      {
                        label: "Outliers",
                        value: profileCol.outlier_count.toLocaleString(),
                      },
                    ]
                  : []),
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between text-xs">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-mono font-medium">{value}</span>
                </div>
              ))}
            </div>

            {profileCol.top_values &&
              Object.keys(profileCol.top_values).length > 0 && (
                <>
                  <Separator />
                  <div className="space-y-1">
                    <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">
                      Top values
                    </p>
                    {Object.entries(profileCol.top_values)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 4)
                      .map(([val, cnt]) => (
                        <div
                          key={val}
                          className="flex justify-between text-xs"
                        >
                          <span
                            className="text-muted-foreground truncate max-w-[110px]"
                            title={val}
                          >
                            {val}
                          </span>
                          <span className="font-mono">{cnt}</span>
                        </div>
                      ))}
                  </div>
                </>
              )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ── Legend ────────────────────────────────────────────────────────────────────

function Legend() {
  return (
    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
      <span className="font-medium text-foreground">Importance:</span>
      {[
        { color: "bg-green-400", label: "High" },
        { color: "bg-yellow-400", label: "Medium" },
        { color: "bg-gray-300", label: "Low" },
      ].map(({ color, label }) => (
        <span key={label} className="flex items-center gap-1">
          <span className={`inline-block h-2 w-2 rounded-sm ${color}`} />
          {label}
        </span>
      ))}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface FeatureGraphViewProps {
  result: AnalyzeResponse;
}

export function FeatureGraphView({ result }: FeatureGraphViewProps) {
  const selectedFeature = useAppStore((s) => s.selectedFeature);
  const setSelectedFeature = useAppStore((s) => s.setSelectedFeature);

  const { initialNodes, initialEdges } = useMemo(() => {
    if (!result.graph) return { initialNodes: [], initialEdges: [] };

    const { nodes: graphNodes, edges: graphEdges } = result.graph;
    const positions = circularLayout(graphNodes.length);

    // Normalise MI scores 0–1 for importance; target column may not have MI
    const miScores = result.profile?.mutual_info ?? [];
    const maxMI = miScores.length > 0 ? Math.max(...miScores.map((m) => m.score)) : 1;

    // graphNodes is string[] — each element is a column name
    const flowNodes: Node<FeatureNodeData>[] = graphNodes.map((name, i) => {
      const rawMI = miScores.find((m) => m.column === name)?.score ?? 0;
      const importance = maxMI > 0 ? rawMI / maxMI : 0;
      return {
        id: name,
        type: "feature",
        position: positions[i],
        data: {
          name,
          importance,
          semantic_label: result.semantic_labels?.[name] ?? null,
        },
        selected: name === selectedFeature,
      };
    });

    const flowEdges: Edge[] = graphEdges.map((e) => {
      const absWeight = Math.abs(e.weight);
      return {
        id: `${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        style: {
          strokeWidth: 1 + absWeight * 4,
          stroke:
            e.edge_type === "correlation"
              ? "hsl(217 91% 60%)"
              : "hsl(270 50% 60%)",
          opacity: 0.4 + absWeight * 0.5,
        },
        animated: false,
      };
    });

    return { initialNodes: flowNodes, initialEdges: flowEdges };
  }, [result.graph, selectedFeature]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handlePaneClick = useCallback(() => {
    setSelectedFeature(null);
  }, [setSelectedFeature]);

  if (!result.graph || result.graph.nodes.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground h-64 flex items-center justify-center">
        Feature graph not available — requires full analysis with graph builder.
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">Feature graph</CardTitle>
          <Legend />
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="relative h-[500px] rounded-b-lg overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={NODE_TYPES}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onPaneClick={handlePaneClick}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.3}
            maxZoom={2}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={16} size={1} />
            <Controls showInteractive={false} />
            <MiniMap
              nodeColor={(n) => {
                const imp = (n.data as FeatureNodeData).importance ?? 0;
                if (imp > 0.6) return "#4ade80";
                if (imp > 0.3) return "#facc15";
                return "#d1d5db";
              }}
              pannable
              zoomable
            />

            {selectedFeature && (
              <Panel position="top-right" className="m-2">
                <NodeDetailPanel
                  name={selectedFeature}
                  result={result}
                  onClose={() => setSelectedFeature(null)}
                />
              </Panel>
            )}
          </ReactFlow>
        </div>
      </CardContent>
    </Card>
  );
}
