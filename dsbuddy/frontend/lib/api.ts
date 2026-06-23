import type {
  AnalyzeResponse,
  ChatRequest,
  HealthResponse,
  ProblemType,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly where: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let code = "UNKNOWN";
    let where = "unknown";
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      code = body.code ?? code;
      where = body.where ?? where;
      message = body.error ?? message;
    } catch {
      // body is not JSON — keep defaults
    }
    throw new ApiError(res.status, code, message, where);
  }
  return res.json() as Promise<T>;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`);
  return handleResponse<HealthResponse>(res);
}

export async function analyzeDataset(
  file: File,
  target_column: string,
  problem_type: ProblemType,
  domain?: string
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("target_column", target_column);
  form.append("problem_type", problem_type);
  if (domain) form.append("domain", domain);

  const res = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    body: form,
  });
  return handleResponse<AnalyzeResponse>(res);
}

export type StreamEvent =
  | { step: "scanning" | "scanning_done" | "profiling" | "profiling_done" | "graph" | "graph_done" | "training" | "training_done" | "reasoning"; message: string }
  | { step: "done"; message: string; data: AnalyzeResponse }
  | { step: "error"; message: string };

export async function* analyzeDatasetStream(
  file: File,
  target_column: string,
  problem_type: ProblemType,
  domain?: string
): AsyncGenerator<StreamEvent> {
  const form = new FormData();
  form.append("file", file);
  form.append("target_column", target_column);
  form.append("problem_type", problem_type);
  if (domain) form.append("domain", domain);

  const res = await fetch(`${BASE_URL}/analyze`, { method: "POST", body: form });

  if (!res.ok || !res.body) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body.error ?? message;
    } catch { /* ignore */ }
    yield { step: "error", message };
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data: ")) continue;
      try {
        yield JSON.parse(line.slice(6)) as StreamEvent;
      } catch { /* malformed event, skip */ }
    }
  }
}

export type ChatStreamEvent =
  | { type: "delta"; text: string }
  | { type: "done"; remaining: number }
  | { type: "error"; message: string };

export async function* sendChatMessageStream(
  payload: ChatRequest
): AsyncGenerator<ChatStreamEvent> {
  const res = await fetch(`${BASE_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok || !res.body) {
    let message = `HTTP ${res.status}`;
    try { const b = await res.json(); message = b.detail?.error ?? message; } catch { /* ignore */ }
    yield { type: "error", message };
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data: ")) continue;
      try { yield JSON.parse(line.slice(6)) as ChatStreamEvent; } catch { /* skip */ }
    }
  }
}


export { ApiError };
