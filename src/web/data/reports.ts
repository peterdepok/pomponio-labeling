/**
 * Shared report generation and delivery.
 * Extracted so both AnimalsScreen and the app exit handler can send the daily report.
 */

import type { Animal, Box, Package } from "../hooks/useAppState.ts";
import type { LogEventFn, AuditEntry } from "../hooks/useAuditLog.ts";
import { generateDailyProductionCsv, generateAuditLogCsv, exportCsv } from "./csv.ts";
import { sendReport } from "./email.ts";

interface SendDailyReportParams {
  animals: Animal[];
  boxes: Box[];
  packages: Package[];
  emailRecipient: string;
  logEvent: LogEventFn;
  showToast: (msg: string) => void;
  auditEntries?: AuditEntry[];
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
  auditEntries,
}: SendDailyReportParams): Promise<boolean> {
  if (animals.length === 0) {
    return false;
  }

  const csv = generateDailyProductionCsv(animals, boxes, packages);
  const today = new Date().toLocaleDateString().replace(/\//g, "-");
  const filename = `daily_production_${today}.csv`;

  const exportResult = await exportCsv(csv, filename);
  logEvent("daily_report_exported", { filename, path: exportResult.path });

  // Build audit log attachment if entries were provided
  const extraAttachments: { content: string; filename: string }[] = [];
  if (auditEntries && auditEntries.length > 0) {
    const auditCsv = generateAuditLogCsv(auditEntries);
    const auditFilename = `audit_log_${today}.csv`;
    extraAttachments.push({ content: auditCsv, filename: auditFilename });

    // Also export audit log to disk
    await exportCsv(auditCsv, auditFilename);
  }

  if (emailRecipient) {
    showToast("Sending shift report...");
    const result = await sendReport({
      to: emailRecipient,
      subject: `Pomponio Ranch Shift Report: ${today}`,
      csvContent: csv,
      filename,
      attachments: extraAttachments.length > 0 ? extraAttachments : undefined,
    });

    if (result.ok && result.queued) {
      logEvent("daily_report_emailed", { recipient: emailRecipient, success: true });
      showToast("Email queued, will retry when online.");
    } else if (result.ok) {
      logEvent("daily_report_emailed", { recipient: emailRecipient, success: true });
      showToast(`Shift report emailed to ${emailRecipient}`);
    } else {
      logEvent("daily_report_emailed", { recipient: emailRecipient, success: false });
      showToast(`Email failed: ${result.error || "unknown"}. CSVs saved locally.`);
    }
  }

  return true;
}
