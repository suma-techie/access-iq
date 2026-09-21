import { useEffect, useState } from "react";
import { deleteMyRequest, fetchApplications, fetchGrants, fetchUsers, revokeRequest } from "../api/endpoints";
import ConfirmDialog from "../components/ConfirmDialog";
import StatusPill from "../components/StatusPill";
import type { AccessRequest, Application, User } from "../types";

export default function Revocation() {
  const [grants, setGrants] = useState<AccessRequest[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<AccessRequest | null>(null);
  const [revokeReason, setRevokeReason] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<AccessRequest | null>(null);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchGrants(), fetchApplications(), fetchUsers()])
      .then(([g, a, u]) => {
        setGrants(g);
        setApplications(a);
        setUsers(u);
      })
      .finally(() => setIsLoading(false));
  }, []);

  function appName(id: string) {
    return applications.find((a) => a.id === id)?.name ?? id;
  }
  function userName(id: string) {
    return users.find((u) => u.id === id)?.display_name ?? id;
  }

  async function confirmRevoke() {
    if (!revokeTarget) return;
    setError(null);
    try {
      const updated = await revokeRequest(revokeTarget.id, revokeReason || undefined);
      setGrants((prev) => prev.map((g) => (g.id === revokeTarget.id ? updated : g)));
      setRevokeTarget(null);
      setRevokeReason("");
    } catch {
      setError("Could not revoke this grant");
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setError(null);
    try {
      await deleteMyRequest(deleteTarget.id);
      setGrants((prev) => prev.filter((g) => g.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch {
      setError("Could not delete this record");
    }
  }

  return (
    <div>
      <h1>Revocation</h1>
      <p className="page-subtitle">Currently granted access. Revoking opens a deprovisioning ticket.</p>
      {error && <p className="error">{error}</p>}

      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Application</th>
              <th>Requester</th>
              <th>Permission</th>
              <th>Status</th>
              <th>Granted at</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {grants.map((g) => (
              <tr key={g.id}>
                <td>{appName(g.application_id)}</td>
                <td>{userName(g.requester_id)}</td>
                <td>{g.requested_text}</td>
                <td>
                  <StatusPill status={g.status} />
                </td>
                <td>{g.resolved_at ? new Date(g.resolved_at).toLocaleString() : "—"}</td>
                <td className="row-actions">
                  {g.status === "approved" && (
                    <button className="danger-button" onClick={() => setRevokeTarget(g)}>
                      Revoke
                    </button>
                  )}
                  {g.status === "revoked" && (
                    <>
                      {g.revoke_reason && <span className="hint-text">{g.revoke_reason}</span>}
                      <button className="secondary-button" onClick={() => setDeleteTarget(g)}>
                        Delete
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {grants.length === 0 && (
              <tr>
                <td colSpan={6}>No grants yet.</td>
              </tr>
            )}
          </tbody>
        </table>
        </div>
      )}

      <ConfirmDialog
        open={revokeTarget !== null}
        title="Revoke this access?"
        message={`This opens a deprovisioning ticket for "${revokeTarget?.requested_text}". This can't be undone.`}
        confirmLabel="Revoke"
        danger
        onConfirm={confirmRevoke}
        onCancel={() => {
          setRevokeTarget(null);
          setRevokeReason("");
        }}
      >
        <textarea
          placeholder="Reason (optional)"
          value={revokeReason}
          onChange={(e) => setRevokeReason(e.target.value)}
          rows={2}
        />
      </ConfirmDialog>

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete this record?"
        message="This permanently removes the revoked request from the list. This can't be undone."
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
