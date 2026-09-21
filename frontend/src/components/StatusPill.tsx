import { statusForRequestStatus } from "../theme/colors";

const LABELS: Record<string, string> = {
  pending: "Pending",
  escalated: "Escalated",
  pending_client_approval: "Awaiting client",
  approved: "Approved",
  rejected: "Rejected",
  cannot_verify: "Could not verify",
  revoked: "Revoked",
  cancelled: "Cancelled",
  expired: "Expired",
};

export default function StatusPill({ status }: { status: string }) {
  const color = statusForRequestStatus[status] ?? "var(--status-muted)";
  return (
    <span className="status-pill" style={{ background: `color-mix(in srgb, ${color} 18%, transparent)`, color }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: color, display: "inline-block" }} />
      {LABELS[status] ?? status}
    </span>
  );
}
