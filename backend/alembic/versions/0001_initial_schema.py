
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


DDL = """
-- ============================================================
-- Extensions
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- Identity & org structure
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    display_name    VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    global_role     VARCHAR(20)  NOT NULL DEFAULT 'member'
                        CHECK (global_role IN ('admin', 'manager', 'member')),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_managers ON users(id) WHERE global_role = 'manager' AND is_active;

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NULL,
    name            VARCHAR(255) NOT NULL,
    description     TEXT NULL,
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE applications (
    id                               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                        UUID NULL,
    project_id                       UUID NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    name                             VARCHAR(255) NOT NULL,
    description                      TEXT NULL,
    default_requires_client_approval BOOLEAN NOT NULL DEFAULT FALSE,
    is_active                        BOOLEAN NOT NULL DEFAULT TRUE,
    created_by                       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at                       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_applications_project ON applications(project_id);

-- ============================================================
-- Project-scoped roles & delegation
-- ============================================================

CREATE TABLE application_roles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NULL,
    application_id  UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_name       VARCHAR(30) NOT NULL
                        CHECK (role_name IN ('team_lead', 'application_owner')),
    assigned_by     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at      TIMESTAMPTZ NULL
);

CREATE UNIQUE INDEX uq_application_roles_active
    ON application_roles(application_id, user_id, role_name)
    WHERE revoked_at IS NULL;

CREATE INDEX idx_application_roles_user ON application_roles(user_id) WHERE revoked_at IS NULL;

CREATE TABLE delegations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NULL,
    delegator_id    UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    delegate_id     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    project_id      UUID NULL REFERENCES projects(id) ON DELETE CASCADE,
    application_id  UUID NULL REFERENCES applications(id) ON DELETE CASCADE,
    start_date      DATE NOT NULL DEFAULT current_date,
    end_date        DATE NULL,
    revoked_at      TIMESTAMPTZ NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (project_id IS NULL OR application_id IS NULL)
);

CREATE INDEX idx_delegations_delegate_active
    ON delegations(delegate_id)
    WHERE revoked_at IS NULL;

-- ============================================================
-- Catalog & documents
-- ============================================================

CREATE TABLE catalog_entries (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                UUID NULL,
    application_id           UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    permission_name          VARCHAR(255) NOT NULL,
    permission_key           VARCHAR(255) NOT NULL,
    description              TEXT NULL,
    severity                 VARCHAR(10) NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    requires_client_approval BOOLEAN NULL,
    is_active                BOOLEAN NOT NULL DEFAULT TRUE,
    created_by               UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (application_id, permission_key)
);

CREATE INDEX idx_catalog_entries_app ON catalog_entries(application_id) WHERE is_active;

CREATE TABLE catalog_entry_versions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_entry_id UUID NOT NULL REFERENCES catalog_entries(id) ON DELETE CASCADE,
    version_no       INT NOT NULL,
    snapshot         JSONB NOT NULL,
    change_type      VARCHAR(20) NOT NULL
                         CHECK (change_type IN ('created', 'updated', 'deactivated', 'correction')),
    changed_by       UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (catalog_entry_id, version_no)
);

CREATE TABLE documents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NULL,
    application_id    UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    uploaded_by       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    original_filename VARCHAR(500) NOT NULL,
    file_type         VARCHAR(20) NOT NULL DEFAULT 'pdf',
    storage_url       TEXT NOT NULL,
    parse_status      VARCHAR(20) NOT NULL DEFAULT 'pending'
                          CHECK (parse_status IN ('pending', 'parsed', 'failed')),
    parsed_text       TEXT NULL,
    parsed_at         TIMESTAMPTZ NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_application ON documents(application_id);

-- ============================================================
-- Requests & approvals
-- ============================================================

CREATE TABLE access_requests (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NULL,
    requester_id     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    application_id   UUID NOT NULL REFERENCES applications(id) ON DELETE RESTRICT,
    catalog_entry_id UUID NULL REFERENCES catalog_entries(id) ON DELETE SET NULL,

    requested_text   TEXT NOT NULL,

    severity         VARCHAR(10) NULL CHECK (severity IN ('low', 'medium', 'high')),
    approval_domain  VARCHAR(10) NOT NULL CHECK (approval_domain IN ('internal', 'client')),

    status           VARCHAR(25) NOT NULL DEFAULT 'pending'
                         CHECK (status IN (
                             'pending', 'escalated', 'pending_client_approval', 'approved',
                             'rejected', 'cannot_verify', 'revoked', 'cancelled', 'expired'
                         )),

    source_type      VARCHAR(15) NOT NULL CHECK (source_type IN ('ado_task', 'doc', 'catalog_exact', 'none')),
    source_reference JSONB NULL,
    ai_rationale     TEXT NULL,

    resolved_by      UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    resolved_via     VARCHAR(20) NULL
                         CHECK (resolved_via IN
                             ('auto', 'team_lead', 'application_owner', 'manager', 'delegate', 'client')),
    delegation_id    UUID NULL REFERENCES delegations(id) ON DELETE SET NULL,
    resolution_note  TEXT NULL,
    resolved_at      TIMESTAMPTZ NULL,

    expires_at       TIMESTAMPTZ NULL,
    revoked_at       TIMESTAMPTZ NULL,
    revoked_by       UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    revoke_reason    TEXT NULL,

    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_access_requests_open_by_app
    ON access_requests(application_id, severity) WHERE status IN ('pending', 'escalated');
CREATE INDEX idx_access_requests_requester ON access_requests(requester_id);
CREATE INDEX idx_access_requests_status ON access_requests(status);
CREATE INDEX idx_access_requests_created_at ON access_requests(created_at);

CREATE TABLE catalog_corrections (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_entry_id  UUID NOT NULL REFERENCES catalog_entries(id) ON DELETE CASCADE,
    access_request_id UUID NULL REFERENCES access_requests(id) ON DELETE SET NULL,
    scope             VARCHAR(20) NOT NULL DEFAULT 'single_request'
                          CHECK (scope IN ('single_request', 'global')),
    field_changed     VARCHAR(100) NOT NULL,
    old_value         JSONB NULL,
    new_value         JSONB NOT NULL,
    note              TEXT NULL,
    corrected_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tickets (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_request_id UUID NOT NULL REFERENCES access_requests(id) ON DELETE CASCADE,
    ticket_type       VARCHAR(15) NOT NULL CHECK (ticket_type IN ('servicenow', 'client')),
    external_id       VARCHAR(255) NOT NULL,
    external_status   VARCHAR(20) NOT NULL DEFAULT 'open'
                          CHECK (external_status IN ('open', 'in_progress', 'closed', 'failed')),
    external_url      TEXT NULL,
    raised_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_synced_at    TIMESTAMPTZ NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tickets_request ON tickets(access_request_id);

CREATE TABLE audit_log (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NULL,
    access_request_id UUID NULL REFERENCES access_requests(id) ON DELETE SET NULL,
    actor_type        VARCHAR(10) NOT NULL CHECK (actor_type IN ('agent', 'user', 'system')),
    actor_id          UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    action            VARCHAR(100) NOT NULL,
    details           JSONB NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_request ON audit_log(access_request_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- ============================================================
-- Analytics
-- ============================================================

CREATE VIEW v_request_analytics AS
SELECT
    ar.id,
    ar.application_id,
    a.name           AS application_name,
    ar.severity,
    ar.status,
    ar.approval_domain,
    ar.resolved_via,
    ar.created_at,
    ar.resolved_at,
    EXTRACT(EPOCH FROM (ar.resolved_at - ar.created_at)) / 3600.0 AS turnaround_hours
FROM access_requests ar
JOIN applications a ON a.id = ar.application_id;
"""

DROP_DDL = """
DROP VIEW IF EXISTS v_request_analytics;
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS catalog_corrections;
DROP TABLE IF EXISTS access_requests;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS catalog_entry_versions;
DROP TABLE IF EXISTS catalog_entries;
DROP TABLE IF EXISTS delegations;
DROP TABLE IF EXISTS application_roles;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS users;
"""


def upgrade() -> None:
    op.execute(DDL)


def downgrade() -> None:
    op.execute(DROP_DDL)
