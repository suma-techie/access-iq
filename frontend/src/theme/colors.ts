
export const categorical = [
  "var(--series-1)",
  "var(--series-2)",
  "var(--series-3)",
  "var(--series-4)",
  "var(--series-5)",
  "var(--series-6)",
  "var(--series-7)",
  "var(--series-8)",
];

export const severityRamp: Record<string, string> = {
  low: "var(--severity-low)",
  medium: "var(--severity-medium)",
  high: "var(--severity-high)",
  unclassified: "var(--severity-unclassified)",
};

export const status = {
  good: "var(--status-good)",
  warning: "var(--status-warning)",
  serious: "var(--status-serious)",
  critical: "var(--status-critical)",
  muted: "var(--status-muted)",
};

export const statusForRequestStatus: Record<string, string> = {
  approved: status.good,
  pending: status.warning,
  escalated: status.serious,
  pending_client_approval: status.warning,
  rejected: status.critical,
  revoked: status.critical,
  cannot_verify: status.muted,
  cancelled: status.muted,
  expired: status.muted,
};

export const chrome = {
  gridline: "var(--chart-grid)",
  baseline: "var(--chart-baseline)",
  secondaryInk: "var(--color-muted)",
};
