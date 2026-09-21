import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { adminUpdateUser, createUserAccount, fetchUsers } from "../api/endpoints";
import type { GlobalRole, User } from "../types";

const ROLE_OPTIONS: GlobalRole[] = ["member", "manager", "admin"];

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [globalRole, setGlobalRole] = useState<GlobalRole>("member");
  const [isCreating, setIsCreating] = useState(false);

  function load() {
    setIsLoading(true);
    fetchUsers(true)
      .then(setUsers)
      .finally(() => setIsLoading(false));
  }

  useEffect(load, []);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsCreating(true);
    try {
      const created = await createUserAccount({ email, display_name: displayName, password, global_role: globalRole });
      setUsers((prev) => [...prev, created].sort((a, b) => a.display_name.localeCompare(b.display_name)));
      setEmail("");
      setDisplayName("");
      setPassword("");
      setGlobalRole("member");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? "Could not create user");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleRoleChange(user: User, role: GlobalRole) {
    const updated = await adminUpdateUser(user.id, { global_role: role });
    setUsers((prev) => prev.map((u) => (u.id === user.id ? updated : u)));
  }

  async function handleToggleActive(user: User) {
    const updated = await adminUpdateUser(user.id, { is_active: !user.is_active });
    setUsers((prev) => prev.map((u) => (u.id === user.id ? updated : u)));
  }

  const filtered = users.filter((u) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return u.display_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
  });

  return (
    <div>
      <h1>Users</h1>
      <p className="page-subtitle">
        Creating accounts and granting the manager/admin role is admin-only. Managers assign project-level roles
        (Team Lead, Application Owner, Developer, QA, ...) from an application's Roles tab.
      </p>

      <form className="inline-form" onSubmit={handleCreate}>
        <input placeholder="firstname.lastname@accessiq.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input placeholder="Display name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
        <input placeholder="Temporary password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <select value={globalRole} onChange={(e) => setGlobalRole(e.target.value as GlobalRole)}>
          {ROLE_OPTIONS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <button type="submit" disabled={isCreating}>
          {isCreating ? "Creating..." : "Create user"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}

      <input className="requester-search" style={{ maxWidth: 320, marginBottom: "0.75rem" }} placeholder="Search by name or email..." value={search} onChange={(e) => setSearch(e.target.value)} />

      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Global role</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr key={u.id}>
                <td>{u.display_name}</td>
                <td>{u.email}</td>
                <td>
                  <select value={u.global_role} onChange={(e) => handleRoleChange(u, e.target.value as GlobalRole)}>
                    {ROLE_OPTIONS.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </td>
                <td>{u.is_active ? "Active" : "Deactivated"}</td>
                <td>
                  <button className="secondary-button" onClick={() => handleToggleActive(u)}>
                    {u.is_active ? "Deactivate" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5}>No matching users.</td>
              </tr>
            )}
          </tbody>
        </table>
        </div>
      )}
    </div>
  );
}
