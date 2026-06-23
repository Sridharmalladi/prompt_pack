"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { sendChatMessageStream } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import type { AnalyzeResponse } from "@/lib/types";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { MessageCircleIcon, SendIcon, AlertCircleIcon } from "lucide-react";
import { useIsMobile } from "@/lib/hooks";

// ── Helpers ────────────────────────────────────────────────────────────────────

function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s+/g, "")          // ## headers
    .replace(/\*\*(.+?)\*\*/g, "$1")    // **bold**
    .replace(/\*(.+?)\*/g, "$1")        // *italic*
    .replace(/`(.+?)`/g, "$1")          // `code`
    .replace(/^\s*[-*]\s+/gm, "")       // - bullets
    .replace(/^\s*\d+\.\s+/gm, "")      // 1. lists
    .trim();
}

// ── Loading dots ───────────────────────────────────────────────────────────────

function LoadingDots() {
  return (
    <div className="flex items-center gap-1 py-1 px-0.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1 w-1 rounded-full bg-muted-foreground/40 animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
}

// ── Message bubble ─────────────────────────────────────────────────────────────

function MessageBubble({ role, content, streaming }: { role: "user" | "assistant"; content: string; streaming?: boolean }) {
  const isUser = role === "user";
  return (
    <div className={cn("flex gap-2.5", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={cn(
        "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[9px] font-bold mt-0.5",
        isUser ? "bg-foreground text-background border-foreground" : "bg-muted border-border text-muted-foreground"
      )}>
        {isUser ? "U" : "AI"}
      </div>
      <div className={cn(
        "max-w-[82%] rounded px-3 py-2 text-xs leading-relaxed",
        isUser
          ? "bg-foreground text-background rounded-tr-none"
          : "bg-muted text-foreground rounded-tl-none"
      )}>
        {content || (streaming && <LoadingDots />)}
        {streaming && content && (
          <span className="inline-block w-0.5 h-3 bg-current ml-0.5 animate-pulse align-middle" />
        )}
      </div>
    </div>
  );
}

// ── Suggested prompts ──────────────────────────────────────────────────────────

const SUGGESTIONS = [
  "What's the biggest data quality issue?",
  "Which features matter most for the target?",
  "What model would you recommend and why?",
  "Are there any leakage risks I should know about?",
];

// ── Main ───────────────────────────────────────────────────────────────────────

interface ChatDrawerProps {
  result: AnalyzeResponse;
}

export function ChatDrawer({ result }: ChatDrawerProps) {
  const isMobile = useIsMobile();
  const {
    messages,
    messagesRemaining,
    isChatOpen,
    addMessage,
    setMessagesRemaining,
    setChatOpen,
    sessionId,
  } = useAppStore();

  const [input, setInput] = useState("");
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const isStreaming = streamingText !== null;
  const bottomRef = useRef<HTMLDivElement>(null);
  const accRef = useRef("");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText, isChatOpen]);

  const contextSummary = [
    result.insights?.summary ?? `Dataset: ${result.file_info.filename}, ${result.file_info.row_count} rows, ${result.file_info.column_count} columns.`,
    result.profile ? `Columns: ${result.profile.columns.map(c => `${c.name} (${c.dtype}, ${c.missing_pct.toFixed(1)}% missing)`).slice(0, 15).join("; ")}` : "",
    result.model_scores?.length ? `Model scores: ${result.model_scores.map(m => { const e = Object.entries(m.metrics)[0]; return e ? `${m.model_name}: ${e[0]}=${(e[1]*100).toFixed(1)}%` : m.model_name; }).join(", ")}` : "",
  ].filter(Boolean).join("\n\n");

  const contextInsights = result.insights
    ? JSON.stringify({
        recommendations: result.insights.recommendations?.slice(0, 5),
        insights: result.insights.insights?.slice(0, 8),
        leakage_risk_columns: result.insights.leakage_risk_columns,
      })
    : undefined;

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || isStreaming || messagesRemaining <= 0) return;

    setErrorMsg(null);
    addMessage({ role: "user", content: question });
    setStreamingText("");
    accRef.current = "";

    try {
      for await (const event of sendChatMessageStream({
        session_id: sessionId ?? "default",
        question,
        context_summary: contextSummary,
        context_insights: contextInsights,
      })) {
        if (event.type === "delta") {
          accRef.current += event.text;
          setStreamingText(accRef.current);
        } else if (event.type === "done") {
          addMessage({ role: "assistant", content: stripMarkdown(accRef.current) });
          setStreamingText(null);
          setMessagesRemaining(event.remaining);
        } else if (event.type === "error") {
          setErrorMsg(event.message);
          setStreamingText(null);
        }
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Connection error. Is the backend running?");
      setStreamingText(null);
    }
  }, [isStreaming, messagesRemaining, sessionId, contextSummary, contextInsights, addMessage, setMessagesRemaining]);

  function handleSend() {
    const q = input.trim();
    if (!q) return;
    setInput("");
    sendMessage(q);
  }

  const exhausted = messagesRemaining <= 0;

  return (
    <>
      {/* Floating trigger */}
      <button
        onClick={() => setChatOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-foreground px-4 py-2.5 text-xs font-medium text-background shadow-lg hover:opacity-80 transition-opacity"
      >
        <MessageCircleIcon className="h-3.5 w-3.5" />
        Ask AI
        <span className="opacity-60">·</span>
        <span className="opacity-60">{messagesRemaining} left</span>
      </button>

      <Sheet open={isChatOpen} onOpenChange={setChatOpen}>
        <SheetContent
          side={isMobile ? "bottom" : "right"}
          className={cn(
            "flex flex-col p-0 gap-0 bg-background border-border",
            isMobile ? "h-[80vh] rounded-t-xl" : "w-full sm:max-w-[420px]"
          )}
        >
          {/* Header */}
          <SheetHeader className="px-5 py-4 border-b border-border/60 shrink-0">
            <div className="flex items-center justify-between">
              <SheetTitle className="text-sm font-semibold text-foreground">
                Ask about your data
              </SheetTitle>
              <span className={cn(
                "text-[10px] font-medium px-2 py-0.5 rounded border",
                exhausted
                  ? "border-destructive/40 text-destructive bg-destructive/5"
                  : "border-border text-muted-foreground"
              )}>
                {messagesRemaining} / 10 remaining
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground text-left">
              {result.file_info.filename} · {result.file_info.row_count.toLocaleString()} rows
            </p>
          </SheetHeader>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4 min-h-0">
            {messages.length === 0 ? (
              <div className="space-y-4">
                <p className="text-xs text-muted-foreground">
                  Ask anything about this dataset — quality issues, which features matter, what model to try, why certain values look off.
                </p>
                <div className="space-y-1.5">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => sendMessage(s)}
                      disabled={isStreaming || exhausted}
                      className="w-full text-left rounded border border-border/60 px-3 py-2 text-xs text-muted-foreground hover:border-foreground/25 hover:text-foreground hover:bg-secondary/60 transition-all disabled:opacity-40"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, i) => (
                  <MessageBubble key={i} role={msg.role} content={msg.content} />
                ))}
                {streamingText !== null && (
                  <MessageBubble role="assistant" content={stripMarkdown(streamingText)} streaming />
                )}
              </>
            )}

            {errorMsg && (
              <div className="flex items-start gap-2 rounded border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
                <AlertCircleIcon className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                {errorMsg}
              </div>
            )}

            {exhausted && messages.length > 0 && (
              <p className="text-center text-[10px] text-muted-foreground pt-2">
                You&apos;ve used all 10 messages. Start a new analysis to continue.
              </p>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-5 py-4 border-t border-border/60 shrink-0 space-y-2">
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
                }}
                disabled={exhausted || isStreaming}
                placeholder={exhausted ? "No messages remaining" : "Ask about this dataset…"}
                rows={2}
                className="flex-1 resize-none rounded border border-border bg-card px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-foreground/20 disabled:opacity-40 disabled:cursor-not-allowed"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || exhausted || isStreaming}
                className="h-9 w-9 shrink-0 flex items-center justify-center rounded bg-foreground text-background hover:opacity-80 transition-opacity disabled:opacity-30"
                aria-label="Send"
              >
                <SendIcon className="h-3.5 w-3.5" />
              </button>
            </div>
            <p className="text-[10px] text-muted-foreground">Shift+Enter for new line</p>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
