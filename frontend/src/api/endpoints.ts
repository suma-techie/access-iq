import { apiClient } from "./client";
import type {
  AccessRequest,
  Application,
  ApplicationRoleAssignment,
  ApplicationRoleName,
  CatalogEntry,
  ChatMessage,
  Delegation,
  DocumentMeta,
  Project,
  Ticket,
  User,
} from "../types";

export async function login(email: string, password: string) {
  const { data } = await apiClient.post<{ access_token: string; user: User }>("/auth/login", {
    email,
    password,
  });
  return data;
}

export async function fetchMe() {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}

export async function fetchUsers(includeInactive = false) {
  const { data } = await apiClient.get<User[]>("/users", { params: includeInactive ? { include_inactive: true } : undefined });
  return data;
}

export async function createUserAccount(payload: { email: string; display_name: string; password: string; global_role: string }) {
  const { data } = await apiClient.post<User>("/users", payload);
  return data;
}

export async function adminUpdateUser(userId: string, payload: { global_role?: string; is_active?: boolean }) {
  const { data } = await apiClient.patch<User>(`/users/${userId}`, payload);
  return data;
}

export async function updateMyProfile(payload: { phone_number?: string; office_location?: string }) {
  const { data } = await apiClient.patch<User>("/users/me", payload);
  return data;
}

export async function uploadMyAvatar(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<User>("/users/me/avatar", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function changeMyPassword(currentPassword: string, newPassword: string) {
  await apiClient.post("/users/me/change-password", { current_password: currentPassword, new_password: newPassword });
}

export function avatarUrl(userId: string): string {
  const base = apiClient.defaults.baseURL ?? "";
  return `${base}/users/${userId}/avatar`;
}

export async function fetchProjects() {
  const { data } = await apiClient.get<Project[]>("/projects");
  return data;
}

export async function createProject(payload: { name: string; description?: string }) {
  const { data } = await apiClient.post<Project>("/projects", payload);
  return data;
}

export async function updateProject(projectId: string, payload: { name?: string; description?: string }) {
  const { data } = await apiClient.patch<Project>(`/projects/${projectId}`, payload);
  return data;
}

export async function fetchApplications(projectId?: string) {
  const { data } = await apiClient.get<Application[]>("/applications", {
    params: projectId ? { project_id: projectId } : undefined,
  });
  return data;
}

export async function createApplication(payload: {
  project_id: string;
  name: string;
  description?: string;
  default_requires_client_approval?: boolean;
}) {
  const { data } = await apiClient.post<Application>("/applications", payload);
  return data;
}

export async function updateApplication(
  applicationId: string,
  payload: { name?: string; description?: string; default_requires_client_approval?: boolean }
) {
  const { data } = await apiClient.patch<Application>(`/applications/${applicationId}`, payload);
  return data;
}

export async function fetchApplicationRoles(applicationId: string) {
  const { data } = await apiClient.get<ApplicationRoleAssignment[]>(
    `/applications/${applicationId}/roles`
  );
  return data;
}

export async function assignApplicationRole(
  applicationId: string,
  payload: { user_id: string; role_name: ApplicationRoleName }
) {
  const { data } = await apiClient.post<ApplicationRoleAssignment>(
    `/applications/${applicationId}/roles`,
    payload
  );
  return data;
}

export async function revokeApplicationRole(applicationId: string, roleId: string) {
  await apiClient.delete(`/applications/${applicationId}/roles/${roleId}`);
}

export async function updateApplicationRole(
  applicationId: string,
  roleId: string,
  roleName: ApplicationRoleName
) {
  const { data } = await apiClient.patch<ApplicationRoleAssignment>(`/applications/${applicationId}/roles/${roleId}`, {
    role_name: roleName,
  });
  return data;
}

export async function fetchCatalogEntries(applicationId: string) {
  const { data } = await apiClient.get<CatalogEntry[]>(`/applications/${applicationId}/catalog`);
  return data;
}

export async function createCatalogEntry(
  applicationId: string,
  payload: { permission_name: string; permission_key: string; description?: string; severity: string; requires_client_approval?: boolean | null }
) {
  const { data } = await apiClient.post<CatalogEntry>(`/applications/${applicationId}/catalog`, payload);
  return data;
}

export async function deactivateCatalogEntry(applicationId: string, entryId: string) {
  await apiClient.delete(`/applications/${applicationId}/catalog/${entryId}`);
}

export async function updateCatalogEntry(
  applicationId: string,
  entryId: string,
  payload: { permission_name?: string; description?: string; severity?: string; requires_client_approval?: boolean | null }
) {
  const { data } = await apiClient.patch<CatalogEntry>(`/applications/${applicationId}/catalog/${entryId}`, payload);
  return data;
}

export async function fetchDocuments(applicationId: string) {
  const { data } = await apiClient.get<DocumentMeta[]>(`/applications/${applicationId}/documents`);
  return data;
}

export async function uploadDocument(applicationId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<DocumentMeta>(`/applications/${applicationId}/documents`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteDocument(applicationId: string, documentId: string) {
  await apiClient.delete(`/applications/${applicationId}/documents/${documentId}`);
}

export async function linkDocument(applicationId: string, payload: { file_type: "ado_link" | "jira_link"; label: string; url: string }) {
  const { data } = await apiClient.post<DocumentMeta>(`/applications/${applicationId}/documents/link`, payload);
  return data;
}

export async function sendChatMessage(applicationId: string | null, messages: ChatMessage[]) {
  const { data } = await apiClient.post<{
    reply: string;
    created_requests: AccessRequest[];
    resolved_application_id: string | null;
    resolved_application_name: string | null;
  }>("/chat", {
    application_id: applicationId,
    messages,
  });
  return data;
}

export async function requestExplicitReview(requestId: string) {
  const { data } = await apiClient.post<AccessRequest>(`/requests/${requestId}/request-review`);
  return data;
}

export async function deleteMyRequest(requestId: string) {
  await apiClient.delete(`/requests/${requestId}`);
}

export async function fetchRequests(scope: "mine" | "approvals" | "client") {
  const { data } = await apiClient.get<AccessRequest[]>("/requests", { params: { scope } });
  return data;
}

export async function fetchRequest(requestId: string) {
  const { data } = await apiClient.get<AccessRequest>(`/requests/${requestId}`);
  return data;
}

export async function approveRequest(requestId: string) {
  const { data } = await apiClient.post<AccessRequest>(`/requests/${requestId}/approve`);
  return data;
}

export async function rejectRequest(requestId: string, note?: string) {
  const { data } = await apiClient.post<AccessRequest>(`/requests/${requestId}/reject`, { note });
  return data;
}

export async function cancelRequest(requestId: string) {
  const { data } = await apiClient.post<AccessRequest>(`/requests/${requestId}/cancel`);
  return data;
}

export async function revokeRequest(requestId: string, reason?: string) {
  const { data } = await apiClient.post<AccessRequest>(`/requests/${requestId}/revoke`, { reason });
  return data;
}

export async function recordClientDecision(requestId: string, decision: "approved" | "rejected", note?: string) {
  const { data } = await apiClient.post<AccessRequest>(`/requests/${requestId}/client-status`, { decision, note });
  return data;
}

export async function fetchGrants(applicationId?: string) {
  const { data } = await apiClient.get<AccessRequest[]>("/grants", { params: applicationId ? { application_id: applicationId } : undefined });
  return data;
}

export async function fetchTickets(requestId: string) {
  const { data } = await apiClient.get<Ticket[]>(`/requests/${requestId}/tickets`);
  return data;
}

export async function updateTicketStatus(ticketId: string, externalStatus: string) {
  const { data } = await apiClient.patch<Ticket>(`/tickets/${ticketId}`, { external_status: externalStatus });
  return data;
}

export async function fetchDelegations() {
  const { data } = await apiClient.get<Delegation[]>("/delegations");
  return data;
}

export async function createDelegation(payload: { delegate_id: string; project_id?: string | null; application_id?: string | null; end_date?: string | null }) {
  const { data } = await apiClient.post<Delegation>("/delegations", payload);
  return data;
}

export async function revokeDelegation(delegationId: string) {
  await apiClient.delete(`/delegations/${delegationId}`);
}

export async function fetchAnalyticsSummary() {
  const { data } = await apiClient.get("/analytics/summary");
  return data as { total: number; pending: number; approved: number; rejected: number; awaiting_client: number };
}

export async function fetchRequestsOverTime(days = 30) {
  const { data } = await apiClient.get("/analytics/requests-over-time", { params: { days } });
  return data as { date: string; count: number }[];
}

export async function fetchStatusBreakdown() {
  const { data } = await apiClient.get("/analytics/status-breakdown");
  return data as { status: string; count: number }[];
}

export async function fetchApprovalModeBreakdown() {
  const { data } = await apiClient.get("/analytics/approval-mode-breakdown");
  return data as { auto: number; manual: number; by_resolved_via: { resolved_via: string; count: number }[] };
}

export async function fetchSeverityBreakdown() {
  const { data } = await apiClient.get("/analytics/severity-breakdown");
  return data as { severity: string; count: number }[];
}

export async function fetchByApplication() {
  const { data } = await apiClient.get("/analytics/by-application");
  return data as { application: string; count: number }[];
}

export async function fetchTurnaroundTime() {
  const { data } = await apiClient.get("/analytics/turnaround-time");
  return data as Record<string, { severity: string; avg_hours: number | null; median_hours: number | null; count: number }[]>;
}
