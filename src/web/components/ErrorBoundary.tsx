/**
 * Global error boundary. Catches unhandled React render errors and shows
 * a recovery screen with a large "Restart App" button and auto-reload
 * countdown. Uses inline styles exclusively so the error screen renders
 * even if the CSS pipeline (Tailwind) is broken.
 */

import { Component } from "react";
import type { ReactNode, ErrorInfo } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  countdown: number;
}

const AUTO_RELOAD_SECONDS = 15;

export class ErrorBoundary extends Component<Props, State> {
  private timer: ReturnType<typeof setInterval> | null = null;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, countdown: AUTO_RELOAD_SECONDS };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error, countdown: AUTO_RELOAD_SECONDS };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("[ErrorBoundary] Uncaught render error:", error, errorInfo);
  }

  componentDidUpdate(_prevProps: Props, prevState: State): void {
    if (this.state.hasError && !prevState.hasError) {
      this.timer = setInterval(() => {
        this.setState(prev => {
          if (prev.countdown <= 1) {
            window.location.reload();
            return prev;
          }
          return { ...prev, countdown: prev.countdown - 1 };
        });
      }, 1000);
    }
  }

  componentWillUnmount(): void {
    if (this.timer) clearInterval(this.timer);
  }

  handleRestart = (): void => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const errorMsg = this.state.error?.message ?? "Unknown error";
      const truncated =
        errorMsg.length > 200 ? errorMsg.slice(0, 200) + "..." : errorMsg;

      return (
        <div
          style={{
            height: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#0d0d1a",
            color: "#e8e8e8",
            fontFamily: "system-ui, sans-serif",
            padding: "2rem",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "4rem", marginBottom: "1.5rem", color: "#ff6b6b" }}>
            &#x26A0;
          </div>
          <h1
            style={{
              fontSize: "2rem",
              fontWeight: "bold",
              marginBottom: "1rem",
              color: "#ff6b6b",
            }}
          >
            Something went wrong
          </h1>
          <p
            style={{
              fontSize: "0.875rem",
              color: "#606080",
              marginBottom: "2rem",
              maxWidth: "500px",
              fontFamily: "monospace",
              wordBreak: "break-word",
            }}
          >
            {truncated}
          </p>
          <button
            onClick={this.handleRestart}
            style={{
              width: "320px",
              height: "80px",
              fontSize: "1.5rem",
              fontWeight: "bold",
              color: "#ffffff",
              background: "linear-gradient(180deg, #e53935, #c62828)",
              border: "none",
              borderRadius: "16px",
              cursor: "pointer",
              boxShadow:
                "0 6px 0 0 #8e0000, 0 8px 12px rgba(0,0,0,0.3)",
              marginBottom: "1.5rem",
            }}
          >
            Restart App
          </button>
          <p style={{ fontSize: "0.875rem", color: "#606080" }}>
            Auto-restarting in {this.state.countdown}s...
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}
