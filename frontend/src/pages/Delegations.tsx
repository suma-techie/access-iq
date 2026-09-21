import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  createDelegation,
  fetchApplications,
  fetchDelegations,
  fetchProjects,
  fetchUsers,
  revokeDelegation,
} from "../api/endpoints";
import UserPicker from "../components/UserPicker";
import type { Application, Delegation, Project, User } from "../types";

type ScopeType = "application" | "project" | "full";

export default function Delegations() {
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [delegateId, setDelegateId] = useState("");
  const [scopeType, setScopeType] = useState<ScopeType>("application");
  const [scopeId, setScopeId] = useState("");
  const [endDate, setEndDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchDelegations(), fetchUsers(), fetchApplications(), fetchProjects()])
      .then(([d, u, a, p]) => {
        setDelegations(d);
        setUsers(u);
        setApplications(a);
        setProjects(p);
      })
      .finally(() => setIsLoading(false));
  }, []);

  function userName(id: string) {
    return users.find((u) => u.id === id)?.display_name ?? id;
  }
  function scopeLabel(d: Delegation) {
    if (d.application_id) return `App: ${applications.find((a) => a.id === d.application_id)?.name ?? d.application_id}`;
    if (d.project_id) return `Project: ${projects.find((p) => p.id === d.project_id)?.name ?? d.project_id}`;
    return "Full scope";
  }
  function statusLabel(d: Delegation) {
    if (d.revoked_at) return "Revoked";
    if (d.end_date && new Date(d.end_date) < new Date()) return "Expired";
    return "Active";
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!delegateId) {
      setError("Select a delegate");
      return;
    }
    if (scopeType !== "full" && !scopeId) {
      setError("Select a scope");
      return;
    }
    try {
      const created = await createDelegation({
        delegate_id: delegateId,
        application_id: scopeType === "application" ? scopeId : null,
        project_id: scopeType === "project" ? scopeId : null,
        end_date: endDate || null,
      });
      setDelegations((prev) => [created, ...prev]);
      setDelegateId("");
      setScopeId("");
      setEndDate("");
    } catch {
      setError("Could not create delegation");
    }
  }

  async function handleRevoke(id: string) {
    await revokeDelegation(id);
    setDelegations((prev) => prev.map((d) => (d.id === id ? { ...d, revoked_at: new Date().toISOString() } : d)));
  }

  return (
    <div>
      <h1>Delegation Management</h1>

      <form className="inline-form" onSubmit={handleSubmit}>
        <UserPicker users={users} value={delegateId} onChange={setDelegateId} placeholder="Delegate to..." />
        <select
          value={scopeType}
          onChange={(e) => {
            setScopeType(e.target.value as ScopeType);
            setScopeId("");
          }}
        >
          <option value="application">Scope: Application</option>
          <option value="project">Scope: Project</option>
          <option value="full">Scope: Full (all)</option>
        </select>
        {scopeType === "application" && (
          <select value={scopeId} onChange={(e) => setScopeId(e.target.value)} required>
            <option value="">Select application</option>
            {applications.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        )}
        {scopeType === "project" && (
          <select value={scopeId} onChange={(e) => setScopeId(e.target.value)} required>
            <option value="">Select project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        )}
        <label className="checkbox-label">
          End date
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </label>
        <button type="submit">Create delegation</button>
      </form>
      {error && <p className="error">{error}</p>}

      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Delegate</th>
              <th>Delegator</th>
              <th>Scope</th>
              <th>Start</th>
              <th>End</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {delegations.map((d) => (
              <tr key={d.id}>
                <td>{userName(d.delegate_id)}</td>
                <td>{userName(d.delegator_id)}</td>
                <td>{scopeLabel(d)}</td>
                <td>{d.start_date}</td>
                <td>{d.end_date ?? "No expiry"}</td>
                <td>{statusLabel(d)}</td>
                <td>{!d.revoked_at && <button onClick={() => handleRevoke(d.id)}>Revoke</button>}</td>
              </tr>
            ))}
            {delegations.length === 0 && (
              <tr>
                <td colSpan={7}>No delegations yet.</td>
              </tr>
            )}
          </tbody>
        </table>
        </div>
      )}
    </div>
  );
}
