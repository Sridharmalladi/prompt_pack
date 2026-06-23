"use client";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        fontFamily: "ui-monospace, monospace",
        background: "var(--background, #fff)",
        color: "var(--foreground, #000)",
      }}
    >
      <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#dc2626", marginBottom: "0.5rem" }}>
        Dashboard crashed — copy the error below and send it
      </h2>
      <pre
        style={{
          background: "#f3f4f6",
          border: "1px solid #e5e7eb",
          borderRadius: "8px",
          padding: "1rem",
          maxWidth: "720px",
          width: "100%",
          overflow: "auto",
          whiteSpace: "pre-wrap",
          fontSize: "0.7rem",
          marginBottom: "1rem",
        }}
      >
        {error.message}
        {"\n\n"}
        {error.stack}
      </pre>
      <button
        onClick={reset}
        style={{
          padding: "0.5rem 1.25rem",
          background: "#111827",
          color: "#fff",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          fontSize: "0.85rem",
        }}
      >
        Try again
      </button>
    </div>
  );
}
