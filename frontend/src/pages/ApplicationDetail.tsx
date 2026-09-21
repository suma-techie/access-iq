import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { useParams } from "react-router-dom";
import {
  assignApplicationRole,
  createCatalogEntry,
  deactivateCatalogEntry,
  deleteDocument,
  fetchApplicationRoles,
  fetchCatalogEntries,
  fetchDocuments,
  fetchUsers,
  linkDocument,
  revokeApplicationRole,
  updateApplicationRole,
  updateCatalogEntry,
  uploadDocument,
} from "../api/endpoints";
import UserPicker from "../components/UserPicker";
import { useAuth } from "../context/AuthContext";
import type {
  ApplicationRoleAssignment,
  ApplicationRoleName,
  CatalogEntry,
  DocumentMeta,
  Severity,
  User,
} from "../types";
import { APPROVAL_GRANTING_ROLES, TEAM_ROLE_LABELS } from "../types";

function RoleSelect({ value, onChange }: { value: ApplicationRoleName; onChange: (v: ApplicationRoleName) => void }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value as ApplicationRoleName)}>
      <optgroup label="Approver">
        {APPROVAL_GRANTING_ROLES.map((r) => (
          <option key={r} value={r}>
            {TEAM_ROLE_LABELS[r]}
          </option>
        ))}
      </optgroup>
      <optgroup label="Team roster (no approval authority)">
        {(Object.keys(TEAM_ROLE_LABELS) as ApplicationRoleName[])
          .filter((r) => !APPROVAL_GRANTING_ROLES.includes(r))
          .map((r) => (
            <option key={r} value={r}>
              {TEAM_ROLE_LABELS[r]}
            </option>
          ))}
      </optgroup>
    </select>
  );
}

type Tab = "roles" | "catalog" | "documents";

export default function ApplicationDetail() {
  const { applicationId } = useParams<{ applicationId: string }>();
  const [tab, setTab] = useState<Tab>("roles");

  if (!applicationId) return null;

  return (
    <div>
      <h1>Application</h1>
      <div className="tab-row">
        <button className={tab === "roles" ? "tab active" : "tab"} onClick={() => setTab("roles")}>
          Roles
        </button>
        <button className={tab === "catalog" ? "tab active" : "tab"} onClick={() => setTab("catalog")}>
          Catalog
        </button>
        <button className={tab === "documents" ? "tab active" : "tab"} onClick={() => setTab("documents")}>
          Documents
        </button>
      </div>
      {tab === "roles" && <RolesTab applicationId={applicationId} />}
      {tab === "catalog" && <CatalogTab applicationId={applicationId} />}
      {tab === "documents" && <DocumentsTab applicationId={applicationId} />}
    </div>
  );
}

function RolesTab({ applicationId }: { applicationId: string }) {
  const { isManager } = useAuth();
  const [roles, setRoles] = useState<ApplicationRoleAssignment[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [userId, setUserId] = useState("");
  const [roleName, setRoleName] = useState<ApplicationRoleName>("team_lead");
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editRoleName, setEditRoleName] = useState<ApplicationRoleName>("team_lead");

  useEffect(() => {
    Promise.all([fetchApplicationRoles(applicationId), fetchUsers()]).then(([r, u]) => {
      setRoles(r);
      setUsers(u);
    });
  }, [applicationId]);

  function userName(id: string) {
    return users.find((u) => u.id === id)?.display_name ?? id;
  }

  const assignableUsers = users.filter((u) => u.global_role !== "admin");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!userId) return;
    setError(null);
    try {
      const created = await assignApplicationRole(applicationId, { user_id: userId, role_name: roleName });
      setRoles((prev) => [created, ...prev]);
      setUserId("");
    } catch {
      setError("Could not assign role (maybe it already exists)");
    }
  }

  async function handleRevoke(roleId: string) {
    await revokeApplicationRole(applicationId, roleId);
    setRoles((prev) => prev.map((r) => (r.id === roleId ? { ...r, revoked_at: new Date().toISOString() } : r)));
  }

  function startEdit(role: ApplicationRoleAssignment) {
    setEditingId(role.id);
    setEditRoleName(role.role_name);
  }

  async function saveEdit(roleId: string) {
    try {
      const updated = await updateApplicationRole(applicationId, roleId, editRoleName);
      setRoles((prev) => prev.map((r) => (r.id === roleId ? updated : r)));
      setEditingId(null);
    } catch {
      setError("Could not update role");
    }
  }

  return (
    <div>
      {isManager && (
        <form className="inline-form" onSubmit={handleSubmit}>
          <UserPicker users={assignableUsers} value={userId} onChange={setUserId} placeholder="Search employee by name or email..." />
          <RoleSelect value={roleName} onChange={setRoleName} />
          <button type="submit">Assign role</button>
        </form>
      )}
      {error && <p className="error">{error}</p>}
      <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Role</th>
            <th>Assigned by</th>
            <th>Assigned at</th>
            <th>Status</th>
            {isManager && <th />}
          </tr>
        </thead>
        <tbody>
          {roles.map((role) => (
            <tr key={role.id}>
              <td>{userName(role.user_id)}</td>
              <td>
                {editingId === role.id ? (
                  <RoleSelect value={editRoleName} onChange={setEditRoleName} />
                ) : (
                  TEAM_ROLE_LABELS[role.role_name]
                )}
              </td>
              <td>{userName(role.assigned_by)}</td>
              <td>{new Date(role.assigned_at).toLocaleDateString()}</td>
              <td>{role.revoked_at ? "Revoked" : "Active"}</td>
              {isManager && (
                <td className="row-actions">
                  {!role.revoked_at &&
                    (editingId === role.id ? (
                      <>
                        <button onClick={() => saveEdit(role.id)}>Save</button>
                        <button className="secondary-button" onClick={() => setEditingId(null)}>
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button className="secondary-button" onClick={() => startEdit(role)}>
                          Edit
                        </button>
                        <button onClick={() => handleRevoke(role.id)}>Remove</button>
                      </>
                    ))}
                </td>
              )}
            </tr>
          ))}
          {roles.length === 0 && (
            <tr>
              <td colSpan={isManager ? 6 : 5}>No role assignments yet.</td>
            </tr>
          )}
        </tbody>
      </table>
      </div>
    </div>
  );
}

function CatalogTab({ applicationId }: { applicationId: string }) {
  const [entries, setEntries] = useState<CatalogEntry[]>([]);
  const [name, setName] = useState("");
  const [key, setKey] = useState("");
  const [severity, setSeverity] = useState<Severity>("low");
  const [requiresClient, setRequiresClient] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editEntry, setEditEntry] = useState<{ permission_name: string; severity: Severity; requires_client_approval: boolean }>({
    permission_name: "",
    severity: "low",
    requires_client_approval: false,
  });

  useEffect(() => {
    fetchCatalogEntries(applicationId).then(setEntries);
  }, [applicationId]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const created = await createCatalogEntry(applicationId, {
        permission_name: name,
        permission_key: key,
        severity,
        requires_client_approval: requiresClient || null,
      });
      setEntries((prev) => [...prev, created].sort((a, b) => a.permission_name.localeCompare(b.permission_name)));
      setName("");
      setKey("");
      setRequiresClient(false);
    } catch {
      setError("Could not create entry (permission_key may already exist)");
    }
  }

  async function handleDeactivate(id: string) {
    await deactivateCatalogEntry(applicationId, id);
    setEntries((prev) => prev.filter((e) => e.id !== id));
  }

  function startEdit(entry: CatalogEntry) {
    setEditingId(entry.id);
    setEditEntry({
      permission_name: entry.permission_name,
      severity: entry.severity,
      requires_client_approval: entry.requires_client_approval ?? false,
    });
  }

  async function saveEdit(id: string) {
    try {
      const updated = await updateCatalogEntry(applicationId, id, editEntry);
      setEntries((prev) => prev.map((e) => (e.id === id ? updated : e)));
      setEditingId(null);
    } catch {
      setError("Could not update entry");
    }
  }

  return (
    <div>
      <p className="page-subtitle">
        The permission catalog the agent matches natural-language asks against. Add every permission this
        application can grant, with its severity.
      </p>
      <form className="inline-form" onSubmit={handleSubmit}>
        <input placeholder="Permission name" value={name} onChange={(e) => setName(e.target.value)} required />
        <input
          placeholder="Key (unique, e.g. repo_read)"
          value={key}
          onChange={(e) => setKey(e.target.value.replace(/\s+/g, "_").toLowerCase())}
          required
        />
        <select value={severity} onChange={(e) => setSeverity(e.target.value as Severity)}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <label className="checkbox-label">
          <input type="checkbox" checked={requiresClient} onChange={(e) => setRequiresClient(e.target.checked)} />
          Requires client approval
        </label>
        <button type="submit">Add permission</button>
      </form>
      {error && <p className="error">{error}</p>}

      <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Permission</th>
            <th>Key</th>
            <th>Severity</th>
            <th>Client approval</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id}>
              {editingId === entry.id ? (
                <>
                  <td>
                    <input
                      value={editEntry.permission_name}
                      onChange={(e) => setEditEntry((prev) => ({ ...prev, permission_name: e.target.value }))}
                    />
                  </td>
                  <td>{entry.permission_key}</td>
                  <td>
                    <select
                      value={editEntry.severity}
                      onChange={(e) => setEditEntry((prev) => ({ ...prev, severity: e.target.value as Severity }))}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </td>
                  <td>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={editEntry.requires_client_approval}
                        onChange={(e) => setEditEntry((prev) => ({ ...prev, requires_client_approval: e.target.checked }))}
                      />
                      Required
                    </label>
                  </td>
                  <td className="row-actions">
                    <button onClick={() => saveEdit(entry.id)}>Save</button>
                    <button className="secondary-button" onClick={() => setEditingId(null)}>
                      Cancel
                    </button>
                  </td>
                </>
              ) : (
                <>
                  <td>{entry.permission_name}</td>
                  <td>{entry.permission_key}</td>
                  <td>{entry.severity}</td>
                  <td>{entry.requires_client_approval === null ? "Inherit" : entry.requires_client_approval ? "Yes" : "No"}</td>
                  <td className="row-actions">
                    <button className="secondary-button" onClick={() => startEdit(entry)}>
                      Edit
                    </button>
                    <button onClick={() => handleDeactivate(entry.id)}>Deactivate</button>
                  </td>
                </>
              )}
            </tr>
          ))}
          {entries.length === 0 && (
            <tr>
              <td colSpan={5}>No catalog entries yet.</td>
            </tr>
          )}
        </tbody>
      </table>
      </div>
    </div>
  );
}

type DocSourceType = "pdf" | "ado_link" | "jira_link";

function pollDocumentStatus(
  applicationId: string,
  documentId: string,
  setDocuments: (updater: (prev: DocumentMeta[]) => DocumentMeta[]) => void
) {
  let attempts = 0;
  const interval = setInterval(async () => {
    attempts += 1;
    const docs = await fetchDocuments(applicationId);
    const match = docs.find((d) => d.id === documentId);
    if (match && match.parse_status !== "pending") {
      setDocuments((prev) => prev.map((d) => (d.id === documentId ? match : d)));
      clearInterval(interval);
    } else if (attempts >= 8) {
      clearInterval(interval);
    }
  }, 2000);
}

function DocumentsTab({ applicationId }: { applicationId: string }) {
  const [documents, setDocuments] = useState<DocumentMeta[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [sourceType, setSourceType] = useState<DocSourceType>("pdf");
  const [linkLabel, setLinkLabel] = useState("");
  const [linkUrl, setLinkUrl] = useState("");

  useEffect(() => {
    fetchDocuments(applicationId).then(setDocuments);
  }, [applicationId]);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted at MVP");
      return;
    }
    setError(null);
    setIsUploading(true);
    try {
      const created = await uploadDocument(applicationId, file);
      setDocuments((prev) => [created, ...prev]);
      
      pollDocumentStatus(applicationId, created.id, setDocuments);
    } catch {
      setError("Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAddLink(event: FormEvent) {
    event.preventDefault();
    if (sourceType === "pdf" || !linkUrl.trim()) return;
    setError(null);
    try {
      const created = await linkDocument(applicationId, {
        file_type: sourceType,
        label: linkLabel.trim() || linkUrl.trim(),
        url: linkUrl.trim(),
      });
      setDocuments((prev) => [created, ...prev]);
      setLinkLabel("");
      setLinkUrl("");
    } catch {
      setError("Could not add link");
    }
  }

  async function handleDelete(id: string) {
    await deleteDocument(applicationId, id);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }

  function sourceLabel(fileType: string) {
    if (fileType === "ado_link") return "Azure DevOps";
    if (fileType === "jira_link") return "Jira";
    return "PDF";
  }

  return (
    <div>
      <p className="page-subtitle">
        Grounding sources for the agent. Upload a PDF, or link an existing ADO wiki page or Jira ticket — links
        are referenced for citation, not crawled.
      </p>

      <div className="inline-form">
        <select value={sourceType} onChange={(e) => setSourceType(e.target.value as DocSourceType)}>
          <option value="pdf">PDF Upload</option>
          <option value="ado_link">Link Azure DevOps</option>
          <option value="jira_link">Link Jira</option>
        </select>

        {sourceType === "pdf" ? (
          <label className="upload-button">
            {isUploading ? "Uploading..." : "Choose PDF"}
            <input type="file" accept="application/pdf" onChange={handleFileChange} disabled={isUploading} hidden />
          </label>
        ) : (
          <form className="inline-form" style={{ marginBottom: 0 }} onSubmit={handleAddLink}>
            <input placeholder="Label (optional)" value={linkLabel} onChange={(e) => setLinkLabel(e.target.value)} />
            <input
              placeholder={sourceType === "ado_link" ? "https://dev.azure.com/..." : "https://yourteam.atlassian.net/browse/..."}
              value={linkUrl}
              onChange={(e) => setLinkUrl(e.target.value)}
              required
              className="link-url-input"
            />
            <button type="submit">Add link</button>
          </form>
        )}
      </div>
      {error && <p className="error">{error}</p>}

      <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Source</th>
            <th>Type</th>
            <th>Status</th>
            <th>Added</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id}>
              <td>
                {doc.file_type === "pdf" ? (
                  doc.original_filename
                ) : (
                  <a href={doc.storage_url} target="_blank" rel="noreferrer">
                    {doc.original_filename}
                  </a>
                )}
              </td>
              <td>{sourceLabel(doc.file_type)}</td>
              <td>{doc.file_type === "pdf" ? doc.parse_status : "Linked"}</td>
              <td>{new Date(doc.created_at).toLocaleString()}</td>
              <td>
                <button onClick={() => handleDelete(doc.id)}>Remove</button>
              </td>
            </tr>
          ))}
          {documents.length === 0 && (
            <tr>
              <td colSpan={5}>No documents or links added yet.</td>
            </tr>
          )}
        </tbody>
      </table>
      </div>
    </div>
  );
}
