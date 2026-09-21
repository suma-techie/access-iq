import { Fragment, useEffect, useState } from "react";
import { cancelRequest, deleteMyRequest, fetchApplications, fetchRequests, fetchTickets, requestExplicitReview } from "../api/endpoints";
import ConfirmDialog from "../components/ConfirmDialog";
import StatusPill from "../components/StatusPill";
import type { AccessRequest, Application, Ticket } from "../types";

const DELETABLE_STATUSES = new Set(["cannot_verify", "cancelled", "rejected", "expired", "revoked"]);
const TAKE_BACKABLE_STATUSES = new Set(["pending", "escalated", "pending_client_approval"]);

export default function MyRequests() {
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [tickets, setTickets] = useState<Record<string, Ticket[]>>({});
  const [expanded, setExpanded] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [takeBackTarget, setTakeBackTarget] = useState<AccessRequest | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AccessRequest | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchRequests("mine"), fetchApplications()])
      .then(([reqs, apps]) => {
        setRequests(reqs);
        setApplications(apps);
      })
      .finally(() => setIsLoading(false));
  }, []);

  function appName(id: string) {
    return applications.find((a) => a.id === id)?.name ?? id;
  }

  async function toggleExpand(request: AccessRequest) {
    if (expanded === request.id) {
      setExpanded(null);
      return;
    }
    setExpanded(request.id);
    if (!tickets[request.id]) {
      const t = await fetchTickets(request.id);
      setTickets((prev) => ({ ...prev, [request.id]: t }));
    }
  }

  async function confirmTakeBack() {
    if (!takeBackTarget) return;
    setError(null);
    try {
      const updated = await cancelRequest(takeBackTarget.id);
      setRequests((prev) => prev.map((r) => (r.id === takeBackTarget.id ? updated : r)));
      setTakeBackTarget(null);
    } catch {
      setError("Could not take back this request — it may have just been resolved.");
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setError(null);
    try {
      await deleteMyRequest(deleteTarget.id);
      setRequests((prev) => prev.filter((r) => r.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch {
      setError("Could not delete this request");
    }
  }

  async function handleRequestReview(requestId: string) {
    const updated = await requestExplicitReview(requestId);
    setRequests((prev) => prev.map((r) => (r.id === requestId ? updated : r)));
  }

  return (
    <div>
      <h1>My Requests</h1>
      {error && <p className="error">{error}</p>}
      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Application</th>
              <th>Requested</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Requested at</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <Fragment key={r.id}>
                <tr className="clickable-row" onClick={() => toggleExpand(r)}>
                  <td>{appName(r.application_id)}</td>
                  <td>{r.requested_text}</td>
                  <td>{r.severity ?? "unclassified"}</td>
                  <td>
                    <StatusPill status={r.status} />
                  </td>
                  <td>{new Date(r.created_at).toLocaleString()}</td>
                  <td className="row-actions" onClick={(e) => e.stopPropagation()}>
                    {TAKE_BACKABLE_STATUSES.has(r.status) && (
                      <button onClick={() => setTakeBackTarget(r)}>Take back</button>
                    )}
                    {r.status === "cannot_verify" && (
                      <button className="secondary-button" onClick={() => handleRequestReview(r.id)}>
                        Request review
                      </button>
                    )}
                    {DELETABLE_STATUSES.has(r.status) && (
                      <button className="secondary-button" onClick={() => setDeleteTarget(r)}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
                {expanded === r.id && (
                  <tr className="detail-row">
                    <td colSpan={6}>
                      <div className="request-detail">
                        <p>
                          <strong>Source:</strong> {r.source_type}
                          {r.ai_rationale && <> — {r.ai_rationale}</>}
                        </p>
                        {r.resolved_via && (
                          <p>
                            <strong>Resolved via:</strong> {r.resolved_via}
                            {r.resolution_note && <> — {r.resolution_note}</>}
                          </p>
                        )}
                        {tickets[r.id]?.map((t) => (
                          <p key={t.id}>
                            <strong>Ticket {t.external_id}:</strong>{" "}
                            {t.external_status === "closed" ? "Granted" : "Provisioning"} ({t.external_status})
                          </p>
                        ))}
                        {r.status === "cannot_verify" && (
                          <p className="hint-text">
                            Couldn't find this in your ADO tasks or documentation. Use "Request review" to send it
                            to your Team Lead / Application Owner anyway, or upload/update the relevant
                            documentation.
                          </p>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {requests.length === 0 && (
              <tr>
                <td colSpan={6}>No requests yet — try the Chat page.</td>
              </tr>
            )}
          </tbody>
        </table>
        </div>
      )}

      <ConfirmDialog
        open={takeBackTarget !== null}
        title="Take back this request?"
        message={`"${takeBackTarget?.requested_text}" will be withdrawn. You can always ask again later.`}
        confirmLabel="Take back"
        onConfirm={confirmTakeBack}
        onCancel={() => setTakeBackTarget(null)}
      />

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete this request?"
        message="This permanently removes it from your history. This can't be undone."
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
