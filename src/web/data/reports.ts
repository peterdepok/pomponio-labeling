/**
 * Shared report generation and delivery.
 * Extracted so both AnimalsScreen and the app exit handler can send the daily report.
 */

import type { Animal, Box, Package } from "../hooks/useAppState.ts";
import type { LogEventFn } from "../hooks/useAuditLog.ts";
import { generateDailyProductionCsv, downloadCsv } from "./csv.ts";
import { sendReport } from "./email.ts";

interface SendDailyReportParams {
  animals: Animal[];
  boxes: Box[];
  packages: Package[];
  emailRecipient: string;
  logEvent: LogEventFn;
  showToast: (msg: string) => void;
}

/**
 * Generate daily production CSV, download locally, and email if configured.
 * Returns true if the report was generated (regardless of email success).
 */
export async function sendDailyReport({
  animals,
  boxes,
  packages,
  emailRecipient,
  logEvent,
  showToast,
}: SendDailyReportParams): Promise<boolean> {
  if (animals.length === 0) {
    return false;
  }

  const csv = generateDailyProductionCsv(animals, boxes, packages);
  const today = new Date().toLocaleDateString().replace(/\//g, "-");
  const filename = `daily_production_${today}.csv`;

  downloadCsv(csv, filename);
  logEvent("daily_report_downloaded", { filename });

  if (emailRecipient) {
    showToast("Sending daily report...");
    const result = await sendReport({
      to: emailRecipient,
      subject: `Pomponio Ranch Daily Production: ${today}`,
      csvContent: csv,
      filename,
    });

    if (result.ok) {
      logEvent("daily_report_emailed", { recipient: emailRecipient, success: true });
      showToast(`Daily report emailed to ${emailRecipient}`);
    } else {
      logEvent("daily_report_emailed", { recipient: emailRecipient, success: false });
      showToast(`Email failed: ${result.error || "unknown"}. CSV saved locally.`);
    }
  }

  return true;
}
