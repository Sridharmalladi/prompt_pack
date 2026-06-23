"use client";

import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  label?: string;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="rounded-lg border border-destructive/40 bg-destructive/5 px-4 py-3 text-xs text-destructive space-y-1">
          <p className="font-semibold">
            {this.props.label ?? "Section"} failed to render
          </p>
          <p className="font-mono opacity-70 break-all">
            {this.state.error.message}
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
