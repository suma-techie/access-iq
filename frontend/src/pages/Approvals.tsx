import { useEffect, useMemo, useState } from "react";
import { approveRequest, fetchApplications, fetchRequests, fetchUsers, rejectRequest } from "../api/endpoints";
import StatusPill from "../components/StatusPill";
import type { AccessRequest, Application, User } from "../types";

interface RequesterGroup {
  requester: User;
  items: AccessRequest[];
}

export default function Approvals() {
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedRequesterId, setSelectedRequesterId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<Record<string, string>>({});
  const [rejectNote, setRejectNote] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState<Record<string, boolean>>({});

  function loadInitial() {
    setIsLoading(true);
    Promise.all([fetchRequests("approvals"), fetchApplications(), fetchUsers()])
      .then(([reqs, apps, us]) => {
        setRequests(reqs);
        setApplications(apps);
        setUsers(us);
      })
      .finally(() => setIsLoading(false));
  }

  function refreshSilently() {
    fetchRequests("approvals").then(setRequests);
  }

  useEffect(loadInitial, []);

  function appName(id: string) {
    return applications.find((a) => a.id === id)?.name ?? id;
  }

  const groups: RequesterGroup[] = useMemo(() => {
    const byRequester = new Map<string, AccessRequest[]>();
    for (const r of requests) {
      const list = byRequester.get(r.requester_id) ?? [];
      list.push(r);
      byRequester.set(r.requester_id, list);
    }
    const result: RequesterGroup[] = [];
    for (const [requesterId, items] of byRequester) {
      const requester = users.find((u) => u.id === requesterId);
      if (requester) result.push({ requester, items });
    }
    return result.sort((a, b) => a.requester.display_name.localeCompare(b.requester.display_name));
  }, [requests, users]);

  const filteredGroups = groups.filter((g) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return g.requester.display_name.toLowerCase().includes(q) || g.requester.email.toLowerCase().includes(q);
  });

  const selectedGroup = groups.find((g) => g.requester.id === selectedRequesterId) ?? filteredGroups[0] ?? null;

  async function handleApprove(id: string) {
    setActionError((prev) => ({ ...prev, [id]: "" }));
    setSubmitting((prev) => ({ ...prev, [id]: true }));
    try {
      await approveRequest(id);
      setRequests((prev) => prev.filter((r) => r.id !== id));
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setActionError((prev) => ({ ...prev, [id]: detail ?? "This may have just been resolved — refresh." }));
      refreshSilently();
    } finally {
      setSubmitting((prev) => ({ ...prev, [id]: false }));
    }
  }

  async function handleReject(id: string) {
    setActionError((prev) => ({ ...prev, [id]: "" }));
    setSubmitting((prev) => ({ ...prev, [id]: true }));
    try {
      await rejectRequest(id, rejectNote[id] || undefined);
      setRequests((prev) => prev.filter((r) => r.id !== id));
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setActionError((prev) => ({ ...prev, [id]: detail ?? "This may have just been resolved — refresh." }));
      refreshSilently();
    } finally {
      setSubmitting((prev) => ({ ...prev, [id]: false }));
    }
  }

  return (
    <div>
      <h1>Pending Approvals</h1>
      <p className="page-subtitle">
        Approving or rejecting removes an item from your queue immediately — no page refresh needed.
      </p>
      <button onClick={refreshSilently} className="secondary-button standalone-button">
        Refresh
      </button>

      {isLoading ? (
        <p>Loading...</p>
      ) : requests.length === 0 ? (
        <p>Nothing waiting on you right now.</p>
      ) : (
        <div className="approvals-layout">
          <div className="requester-list">
            <input
              className="requester-search"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="requester-list-items">
              {filteredGroups.map((g) => (
                <button
                  key={g.requester.id}
                  className={`requester-item ${selectedGroup?.requester.id === g.requester.id ? "active" : ""}`}
                  onClick={() => setSelectedRequesterId(g.requester.id)}
                >
                  <span className="requester-name">{g.requester.display_name}</span>
                  <span className="requester-count">{g.items.length}</span>
                </button>
              ))}
              {filteredGroups.length === 0 && <p className="hint-text">No matching people.</p>}
            </div>
          </div>

          <div className="approval-list">
            {selectedGroup ? (
              <>
                <h2 className="requester-detail-heading">
                  {selectedGroup.requester.display_name}
                  <span className="hint-text"> · {selectedGroup.requester.email}</span>
                </h2>
                {selectedGroup.items.map((r) => (
                  <div key={r.id} className={`approval-card ${r.status === "escalated" ? "escalated" : ""}`}>
                    <div className="approval-card-header">
                      <div>
                        <strong>{appName(r.application_id)}</strong> — {r.requested_text}
                      </div>
                      <StatusPill status={r.status} />
                    </div>
                    <div className="approval-card-meta">
                      Severity: {r.severity ?? "unclassified"} · Source: {r.source_type}
                    </div>
                    {r.status === "escalated" && (
                      <p className="hint-text escalated-hint">
                        Unverified — {r.ai_rationale || "no confident match found; needs manager judgment."}
                      </p>
                    )}
                    {r.ai_rationale && r.status !== "escalated" && <p className="hint-text">{r.ai_rationale}</p>}

                    <div className="approval-card-actions">
                      <button disabled={submitting[r.id]} onClick={() => handleApprove(r.id)}>
                        {submitting[r.id] ? "Working..." : "Approve"}
                      </button>
                      <input
                        placeholder="Rejection note (optional)"
                        value={rejectNote[r.id] ?? ""}
                        onChange={(e) => setRejectNote((prev) => ({ ...prev, [r.id]: e.target.value }))}
                      />
                      <button className="danger-button" disabled={submitting[r.id]} onClick={() => handleReject(r.id)}>
                        {submitting[r.id] ? "Working..." : "Reject"}
                      </button>
                    </div>
                    {actionError[r.id] && <p className="error">{actionError[r.id]}</p>}
                  </div>
                ))}
              </>
            ) : (
              <p>Select a person to see their pending items.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
