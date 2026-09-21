export type GlobalRole = "admin" | "manager" | "member";

export interface User {
  id: string;
  email: string;
  display_name: string;
  global_role: GlobalRole;
  is_active: boolean;
  phone_number: string | null;
  office_location: string | null;
  avatar_url: string | null;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  default_requires_client_approval: boolean;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type ApplicationRoleName =
  | "team_lead"
  | "application_owner"
  | "developer"
  | "qa"
  | "devops"
  | "business_analyst"
  | "support";

export const APPROVAL_GRANTING_ROLES: ApplicationRoleName[] = ["team_lead", "application_owner"];

export const TEAM_ROLE_LABELS: Record<ApplicationRoleName, string> = {
  team_lead: "Team Lead",
  application_owner: "Application Owner",
  developer: "Developer",
  qa: "QA",
  devops: "DevOps",
  business_analyst: "Business Analyst",
  support: "Support",
};

export interface ApplicationRoleAssignment {
  id: string;
  application_id: string;
  user_id: string;
  role_name: ApplicationRoleName;
  assigned_by: string;
  assigned_at: string;
  revoked_at: string | null;
}

export type Severity = "low" | "medium" | "high";

export interface CatalogEntry {
  id: string;
  application_id: string;
  permission_name: string;
  permission_key: string;
  description: string | null;
  severity: Severity;
  requires_client_approval: boolean | null;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentMeta {
  id: string;
  application_id: string;
  uploaded_by: string;
  original_filename: string;
  file_type: string;
  storage_url: string;
  parse_status: "pending" | "parsed" | "failed";
  parsed_at: string | null;
  created_at: string;
}

export type RequestStatus =
  | "pending"
  | "escalated"
  | "pending_client_approval"
  | "approved"
  | "rejected"
  | "cannot_verify"
  | "revoked"
  | "cancelled"
  | "expired";

export interface AccessRequest {
  id: string;
  requester_id: string;
  application_id: string;
  catalog_entry_id: string | null;
  requested_text: string;
  severity: Severity | null;
  approval_domain: "internal" | "client";
  status: RequestStatus;
  source_type: "ado_task" | "doc" | "catalog_exact" | "none";
  source_reference: Record<string, unknown> | null;
  ai_rationale: string | null;
  resolved_by: string | null;
  resolved_via: string | null;
  delegation_id: string | null;
  resolution_note: string | null;
  resolved_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  revoked_by: string | null;
  revoke_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface Ticket {
  id: string;
  access_request_id: string;
  ticket_type: "servicenow" | "client";
  external_id: string;
  external_status: "open" | "in_progress" | "closed" | "failed";
  external_url: string | null;
  raised_at: string;
  last_synced_at: string | null;
}

export interface Delegation {
  id: string;
  delegator_id: string;
  delegate_id: string;
  project_id: string | null;
  application_id: string | null;
  start_date: string;
  end_date: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
