import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { createProject, fetchProjects, updateProject } from "../api/endpoints";
import { getErrorMessage } from "../api/errors";
import { useAuth } from "../context/AuthContext";
import type { Project } from "../types";

export default function Projects() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const canManage = user?.global_role === "manager" || user?.global_role === "admin";

  useEffect(() => {
    setIsLoading(true);
    fetchProjects()
      .then(setProjects)
      .finally(() => setIsLoading(false));
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const created = await createProject({ name, description: description || undefined });
      setProjects((prev) => [...prev, created].sort((a, b) => a.name.localeCompare(b.name)));
      setName("");
      setDescription("");
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Could not create project"));
    }
  }

  function startEdit(project: Project) {
    setEditingId(project.id);
    setEditName(project.name);
    setEditDescription(project.description ?? "");
  }

  async function saveEdit(id: string) {
    setError(null);
    try {
      const updated = await updateProject(id, { name: editName, description: editDescription });
      setProjects((prev) => prev.map((p) => (p.id === id ? updated : p)));
      setEditingId(null);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Could not update project"));
    }
  }

  return (
    <div>
      <h1>Projects</h1>

      {canManage && (
        <form className="inline-form" onSubmit={handleSubmit}>
          <input
            placeholder="Project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button type="submit">Add project</button>
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
              <th>Description</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => (
              <tr key={project.id}>
                {editingId === project.id ? (
                  <>
                    <td>
                      <input value={editName} onChange={(e) => setEditName(e.target.value)} />
                    </td>
                    <td>
                      <input value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
                    </td>
                    <td className="row-actions">
                      <button onClick={() => saveEdit(project.id)}>Save</button>
                      <button className="secondary-button" onClick={() => setEditingId(null)}>
                        Cancel
                      </button>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{project.name}</td>
                    <td>{project.description ?? "—"}</td>
                    <td className="row-actions">
                      <Link to={`/applications?project_id=${project.id}`}>View applications</Link>
                      {canManage && (
                        <button className="secondary-button" onClick={() => startEdit(project)}>
                          Edit
                        </button>
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}
            {projects.length === 0 && (
              <tr>
                <td colSpan={3}>No projects yet.</td>
              </tr>
            )}
          </tbody>
        </table>
        </div>
      )}
    </div>
  );
}
