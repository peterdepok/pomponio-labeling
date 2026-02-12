/**
 * Email transport abstraction.
 * POSTs report data to /api/send-report (Vercel serverless or local Express).
 * Fails gracefully when offline.
 */

interface SendReportParams {
  to: string;
  subject: string;
  csvContent: string;
  filename: string;
}

interface SendReportResult {
  ok: boolean;
  error?: string;
}

const TIMEOUT_MS = 30_000; // 30-second timeout for email sends

export async function sendReport(params: SendReportParams): Promise<SendReportResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch("/api/send-report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
      signal: controller.signal,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return { ok: false, error: body.error || `HTTP ${res.status}` };
    }

    return { ok: true };
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
