import { useEffect, useState } from "react";
import {
  fetchAnalyticsSummary,
  fetchApprovalModeBreakdown,
  fetchByApplication,
  fetchRequestsOverTime,
  fetchSeverityBreakdown,
  fetchStatusBreakdown,
  fetchTurnaroundTime,
} from "../api/endpoints";
import { BarChart, ChartCard, DonutChart, LineChart, StatTile } from "../components/charts";
import { categorical, severityRamp, statusForRequestStatus } from "../theme/colors";

const STATUS_ORDER = ["approved", "pending", "escalated", "pending_client_approval", "rejected", "cannot_verify", "revoked", "cancelled", "expired"];
const STATUS_LABELS: Record<string, string> = {
  approved: "Approved",
  pending: "Pending",
  escalated: "Escalated",
  pending_client_approval: "Awaiting client",
  rejected: "Rejected",
  cannot_verify: "Could not verify",
  revoked: "Revoked",
  cancelled: "Cancelled",
  expired: "Expired",
};

export default function Dashboard() {
  const [summary, setSummary] = useState<{ total: number; pending: number; approved: number; rejected: number; awaiting_client: number } | null>(null);
  const [overTime, setOverTime] = useState<{ date: string; count: number }[]>([]);
  const [statusBreakdown, setStatusBreakdown] = useState<{ status: string; count: number }[]>([]);
  const [approvalMode, setApprovalMode] = useState<{ auto: number; manual: number } | null>(null);
  const [severity, setSeverity] = useState<{ severity: string; count: number }[]>([]);
  const [byApplication, setByApplication] = useState<{ application: string; count: number }[]>([]);
  const [turnaround, setTurnaround] = useState<Record<string, { severity: string; avg_hours: number | null; count: number }[]>>({});

  useEffect(() => {
    fetchAnalyticsSummary().then(setSummary);
    fetchRequestsOverTime(30).then(setOverTime);
    fetchStatusBreakdown().then(setStatusBreakdown);
    fetchApprovalModeBreakdown().then(setApprovalMode);
    fetchSeverityBreakdown().then(setSeverity);
    fetchByApplication().then(setByApplication);
    fetchTurnaroundTime().then(setTurnaround);
  }, []);

  const statusSegments = STATUS_ORDER.map((s) => ({
    label: STATUS_LABELS[s],
    value: statusBreakdown.find((row) => row.status === s)?.count ?? 0,
    color: statusForRequestStatus[s],
  }));

  return (
    <div>
      <h1>Analytics</h1>

      {summary && (
        <div className="stat-tiles-row">
          <StatTile label="Total requests" value={summary.total} />
          <StatTile label="Pending / escalated" value={summary.pending} />
          <StatTile label="Approved" value={summary.approved} />
          <StatTile label="Rejected" value={summary.rejected} />
          <StatTile label="Awaiting client" value={summary.awaiting_client} />
        </div>
      )}

      <div className="dashboard-grid">
        <ChartCard title="Requests over time" subtitle="Last 30 days">
          <LineChart data={overTime.map((d) => ({ label: d.date, value: d.count }))} color={categorical[0]} />
        </ChartCard>

        <ChartCard title="Status breakdown">
          <DonutChart data={statusSegments} centerLabel="Requests" />
        </ChartCard>

        <ChartCard title="Auto vs. manual approval" subtitle="How much load the agent absorbs">
          {approvalMode ? (
            <DonutChart
              data={[
                { label: "Auto", value: approvalMode.auto, color: categorical[0] },
                { label: "Manual", value: approvalMode.manual, color: categorical[1] },
              ]}
              centerLabel="Resolved"
            />
          ) : (
            <p className="chart-empty">Loading…</p>
          )}
        </ChartCard>

        <ChartCard title="Requests by severity">
          <BarChart
            data={severity.map((s) => ({ label: s.severity, value: s.count, color: severityRamp[s.severity] ?? severityRamp.unclassified }))}
          />
        </ChartCard>

        <ChartCard title="Requests by application">
          <BarChart data={byApplication.map((a, i) => ({ label: a.application, value: a.count, color: categorical[i % categorical.length] }))} />
        </ChartCard>

        <ChartCard title="Approval turnaround (avg hours)" subtitle="Internal only — client turnaround is tracked separately">
          <BarChart
            data={(turnaround.internal ?? []).map((row) => ({
              label: row.severity,
              value: row.avg_hours ?? 0,
              color: severityRamp[row.severity] ?? severityRamp.unclassified,
            }))}
            formatValue={(v) => v.toFixed(1)}
          />
        </ChartCard>

        {(turnaround.client ?? []).some((row) => row.count > 0) && (
          <ChartCard title="Client-controlled turnaround (avg hours)" subtitle="Outside AccessIQ's control">
            <BarChart
              data={(turnaround.client ?? []).map((row) => ({
                label: row.severity,
                value: row.avg_hours ?? 0,
                color: categorical[4],
              }))}
              formatValue={(v) => v.toFixed(1)}
            />
          </ChartCard>
        )}
      </div>
    </div>
  );
}
