/**
 * Email transport abstraction.
 * POSTs report data to /api/email (Flask bridge SMTP sender).
 * When SMTP fails, the bridge queues the email for background retry
 * and returns { ok: true, queued: true }.
 */

interface SendReportParams {
  to: string;
  subject: string;
  csvContent: string;
  filename: string;
}

export interface SendReportResult {
  ok: boolean;
  error?: string;
  /** True when the email was queued for background retry (SMTP unreachable). */
  queued?: boolean;
}

const TIMEOUT_MS = 30_000; // 30-second timeout for email sends

export async function sendReport(params: SendReportParams): Promise<SendReportResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch("/api/email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
      signal: controller.signal,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return { ok: false, error: body.error || `HTTP ${res.status}` };
    }

    const data = await res.json();
    return { ok: data.ok, error: data.error, queued: data.queued };
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return { ok: false, error: "Request timed out (30s)" };
    }
    // Network error (offline, CORS, DNS, etc.)
    const msg = err instanceof Error ? err.message : "Unknown error";
    return { ok: false, error: msg };
  } finally {
    clearTimeout(timer);
  }
}
