import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { createApplication, fetchApplications, fetchProjects, updateApplication } from "../api/endpoints";
import { getErrorMessage } from "../api/errors";
import { useAuth } from "../context/AuthContext";
import type { Application, Project } from "../types";

export default function Applications() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const projectFilter = searchParams.get("project_id") ?? undefined;

  const [applications, setApplications] = useState<Application[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState(projectFilter ?? "");
  const [requiresClientApproval, setRequiresClientApproval] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editRequiresClient, setEditRequiresClient] = useState(false);

  const canCreate = user?.global_role === "manager" || user?.global_role === "admin";

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchApplications(projectFilter), fetchProjects()])
      .then(([apps, projs]) => {
        setApplications(apps);
        setProjects(projs);
      })
      .finally(() => setIsLoading(false));
  }, [projectFilter]);

  function projectName(id: string) {
    return projects.find((p) => p.id === id)?.name ?? id;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!projectId) {
      setError("Select a project");
      return;
    }
    try {
      const created = await createApplication({
        project_id: projectId,
        name,
        description: description || undefined,
        default_requires_client_approval: requiresClientApproval,
      });
      setApplications((prev) => [...prev, created].sort((a, b) => a.name.localeCompare(b.name)));
      setName("");
      setDescription("");
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Could not create application"));
    }
  }

  function startEdit(application: Application) {
    setEditingId(application.id);
    setEditName(application.name);
    setEditDescription(application.description ?? "");
    setEditRequiresClient(application.default_requires_client_approval);
  }

  async function saveEdit(id: string) {
    setError(null);
    try {
      const updated = await updateApplication(id, {
        name: editName,
        description: editDescription,
        default_requires_client_approval: editRequiresClient,
      });
      setApplications((prev) => prev.map((a) => (a.id === id ? updated : a)));
      setEditingId(null);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Could not update application"));
    }
  }

  return (
    <div>
      <h1>Applications{projectFilter ? ` — ${projectName(projectFilter)}` : ""}</h1>

      {canCreate && (
        <form className="inline-form" onSubmit={handleSubmit}>
          <select value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
            <option value="">Select project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input
            placeholder="Application name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={requiresClientApproval}
              onChange={(e) => setRequiresClientApproval(e.target.checked)}
            />
            Requires client approval by default
          </label>
          <button type="submit">Add application</button>
        </form>
      )}
      {error && <p className="error">{error}</p>}

      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Project</th>
              <th>Description</th>
              <th>Client approval default</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {applications.map((application) => (
              <tr key={application.id}>
                {editingId === application.id ? (
                  <>
                    <td>
                      <input value={editName} onChange={(e) => setEditName(e.target.value)} />
                    </td>
                    <td>{projectName(application.project_id)}</td>
                    <td>
                      <input value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
                    </td>
                    <td>
                      <label className="checkbox-label">
                        <input type="checkbox" checked={editRequiresClient} onChange={(e) => setEditRequiresClient(e.target.checked)} />
                        Required
                      </label>
                    </td>
                    <td className="row-actions">
                      <button onClick={() => saveEdit(application.id)}>Save</button>
                      <button className="secondary-button" onClick={() => setEditingId(null)}>
                        Cancel
                      </button>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{application.name}</td>
                    <td>{projectName(application.project_id)}</td>
                    <td>{application.description ?? "—"}</td>
                    <td>{application.default_requires_client_approval ? "Yes" : "No"}</td>
                    <td className="row-actions">
                      <Link to={`/applications/${application.id}`}>Manage</Link>
                      {canCreate && (
                        <button className="secondary-button" onClick={() => startEdit(application)}>
                          Edit
                        </button>
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}
            {applications.length === 0 && (
              <tr>
                <td colSpan={5}>No applications yet.</td>
              </tr>
            )}
          </tbody>
        </table>
        </div>
      )}
    </div>
  );
}
