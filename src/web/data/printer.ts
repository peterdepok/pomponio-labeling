/**
 * Printer API client.
 * Sends generated ZPL to the Flask bridge at POST /api/print,
 * which forwards it to the Zebra ZP 230D via win32print.
 *
 * Pattern matches email.ts: AbortController, timeout, { ok, error } return.
 * Fails gracefully when the bridge is not running (Vite dev mode).
 */

interface PrintResult {
  ok: boolean;
  error?: string;
}

const TIMEOUT_MS = 10_000; // 10-second timeout for print jobs

export async function sendToPrinter(zpl: string): Promise<PrintResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch("/api/print", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zpl }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return { ok: false, error: body.error || `HTTP ${res.status}` };
    }

    const data = await res.json();
    return data;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return { ok: false, error: "Print request timed out (10s)" };
    }
    // Network error (Flask not running, offline, etc.)
    const msg = err instanceof Error ? err.message : "Unknown error";
    return { ok: false, error: msg };
  } finally {
    clearTimeout(timer);
  }
}
