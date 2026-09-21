import { useEffect, useState } from "react";
import { fetchApplications, fetchRequests, fetchTickets, recordClientDecision } from "../api/endpoints";
import { status } from "../theme/colors";
import type { AccessRequest, Application, Ticket } from "../types";

export default function ClientApprovals() {
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [tickets, setTickets] = useState<Record<string, Ticket[]>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);

  function load() {
    setIsLoading(true);
    Promise.all([fetchRequests("client"), fetchApplications()]).then(async ([reqs, apps]) => {
      setRequests(reqs);
      setApplications(apps);
      const ticketEntries = await Promise.all(reqs.map(async (r) => [r.id, await fetchTickets(r.id)] as const));
      setTickets(Object.fromEntries(ticketEntries));
      setIsLoading(false);
    });
  }

  useEffect(load, []);

  function appName(id: string) {
    return applications.find((a) => a.id === id)?.name ?? id;
  }

  async function handleDecision(id: string, decision: "approved" | "rejected") {
    await recordClientDecision(id, decision, notes[id] || undefined);
    setRequests((prev) => prev.filter((r) => r.id !== id));
  }

  return (
    <div>
      <h1>Client-Controlled Approvals</h1>
      <p className="page-subtitle">Outside AccessIQ's control — tracked here, resolved by the client.</p>

      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <div className="approval-list">
          {requests.map((r) => (
            <div key={r.id} className="approval-card">
              <div className="approval-card-header">
                <div>
                  <strong>{appName(r.application_id)}</strong> — {r.requested_text}
                </div>
                <span className="status-pill" style={{ background: `color-mix(in srgb, ${status.warning} 18%, transparent)`, color: status.warning }}>
                  Awaiting client
                </span>
              </div>
              {tickets[r.id]?.map((t) => (
                <p key={t.id} className="hint-text">
                  Client ticket: {t.external_id} ({t.external_status})
                </p>
              ))}
              <div className="approval-card-actions">
                <input
                  placeholder="Note on what the client communicated"
                  value={notes[r.id] ?? ""}
                  onChange={(e) => setNotes((prev) => ({ ...prev, [r.id]: e.target.value }))}
                />
                <button onClick={() => handleDecision(r.id, "approved")}>Record approved</button>
                <button className="danger-button" onClick={() => handleDecision(r.id, "rejected")}>
                  Record rejected
                </button>
              </div>
            </div>
          ))}
          {requests.length === 0 && <p>Nothing awaiting client decision.</p>}
        </div>
      )}
    </div>
  );
}
