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

export async function sendReport(params: SendReportParams): Promise<SendReportResult> {
  try {
    const res = await fetch("/api/send-report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return { ok: false, error: body.error || `HTTP ${res.status}` };
    }

    return { ok: true };
  } catch (err) {
    // Network error (offline, CORS, DNS, etc.)
    const msg = err instanceof Error ? err.message : "Unknown error";
    return { ok: false, error: msg };
  }
}
